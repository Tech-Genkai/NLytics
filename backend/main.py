"""
NLytics Backend - Main Application
Lightweight Flask server with chat-first interface
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import numpy as np
import pandas as pd
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file (in parent directory)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add backend directory to path for imports when running via Gunicorn
import sys
if os.environ.get('FLASK_ENV') == 'production':
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

from services.file_handler import FileHandler
from services.schema_inspector import SchemaInspector
from services.preprocessor import DataPreprocessor
from services.ai_intent_detector import AIIntentDetector
from services.query_refiner import QueryRefiner
from services.query_planner import QueryPlanner
from services.code_generator import CodeGenerator
from services.code_validator import CodeValidator, RetryManager
from services.safe_executor import SafeExecutor
from services.insight_generator import InsightGenerator
from services.answer_synthesizer import AnswerSynthesizer
from models.chat_message import ChatMessage, MessageType
from api.analytics_api import api_blueprint, init_api


def handle_error(session_id: str, error: Exception, context: str = "") -> Dict[str, Any]:
    """Consistent error handling across all endpoints"""
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Log with context
    logger.error(f"Error in {context}: {error_type} - {error_msg}", exc_info=True)
    
    # Create user-friendly message
    friendly_messages = {
        'EmptyDataError': "The file appears to be empty. Please upload a valid CSV or Excel file with data.",
        'ParserError': "I couldn't parse this file. Please ensure it's a valid CSV or Excel file with proper formatting.",
        'MemoryError': "This file is too large to process. Please try a smaller dataset (under 100K rows).",
        'KeyError': "I couldn't find the required data. Please try uploading your file again.",
        'FileNotFoundError': "I couldn't find your uploaded file. Please try uploading again.",
        'ValueError': f"Invalid data: {error_msg}",
        'TimeoutError': "This query took too long to execute. Please try a simpler query.",
    }
    
    user_message = friendly_messages.get(error_type, 
        f"Sorry, I encountered an unexpected error. Please try again or simplify your query.")
    
    error_chat_msg = ChatMessage(
        type=MessageType.ERROR,
        content=f"❌ {user_message}",
        metadata={
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_type': error_type,
            'context': context
        }
    )
    
    if session_id and session_id in sessions:
        save_message_to_session(session_id, error_chat_msg)
    
    return error_chat_msg.to_dict()


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle NumPy types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

app = Flask(__name__, 
            template_folder='../frontend',
            static_folder='../frontend/static')
app.json.encoder = NumpyEncoder  # Use custom encoder for NumPy types

# Configure CORS to allow requests from Render deployment
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000", "https://nlytics.onrender.com"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Session storage folder
SESSION_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'sessions')

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
os.makedirs(SESSION_FOLDER, exist_ok=True)

# Initialize services
file_handler = FileHandler(app.config['UPLOAD_FOLDER'])
schema_inspector = SchemaInspector()
preprocessor = DataPreprocessor()
intent_detector = AIIntentDetector()
query_refiner = QueryRefiner()
query_planner = QueryPlanner()
code_generator = CodeGenerator()
code_validator = CodeValidator()
retry_manager = RetryManager(max_retries=3)
safe_executor = SafeExecutor(timeout_seconds=30)
insight_generator = InsightGenerator()
answer_synthesizer = AnswerSynthesizer()

# File-based session store (works across multiple Gunicorn workers)
class FileSessionStore:
    """Thread-safe file-based session storage for multi-worker deployments"""
    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_session_path(self, session_id):
        return os.path.join(self.storage_dir, f"{session_id}.json")
    
    def __contains__(self, session_id):
        return os.path.exists(self._get_session_path(session_id))
    
    def __getitem__(self, session_id):
        path = self._get_session_path(session_id)
        if not os.path.exists(path):
            raise KeyError(f"Session {session_id} not found")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            raise KeyError(f"Session {session_id} corrupted")
    
    def __setitem__(self, session_id, value):
        path = self._get_session_path(session_id)
        try:
            with open(path, 'w') as f:
                json.dump(value, f)
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
    
    def get(self, session_id, default=None):
        try:
            return self[session_id]
        except KeyError:
            return default
    
    def keys(self):
        return [f.replace('.json', '') for f in os.listdir(self.storage_dir) if f.endswith('.json')]

sessions = FileSessionStore(SESSION_FOLDER)


def save_message_to_session(session_id: str, message: ChatMessage):
    """Helper to append message and save session atomically"""
    if session_id in sessions:
        session_data = sessions[session_id]
        session_data['messages'].append(message.to_dict())
        sessions[session_id] = session_data


# Initialize REST API with service instances
service_dict = {
    'file_handler': file_handler,
    'schema_inspector': schema_inspector,
    'preprocessor': preprocessor,
    'intent_detector': intent_detector,
    'query_refiner': query_refiner,
    'query_planner': query_planner,
    'code_generator': code_generator,
    'code_validator': code_validator,
    'safe_executor': safe_executor,
    'insight_generator': insight_generator,
    'answer_synthesizer': answer_synthesizer
}
init_api(service_dict, sessions)

# Register API blueprint
app.register_blueprint(api_blueprint)


def convert_numpy_types(obj):
    """Recursively convert NumPy types to native Python types"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')


@app.route('/logo.png')
def serve_logo():
    """Serve the logo file"""
    from flask import send_file
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'logo.png')
    return send_file(logo_path, mimetype='image/png')


@app.route('/api/session/new', methods=['POST'])
def new_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    session_data = {
        'id': session_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'messages': [],
        'dataset': None,
        'context': {}
    }
    sessions[session_id] = session_data
    
    welcome_msg = ChatMessage(
        type=MessageType.SYSTEM,
        content="👋 Welcome to NLytics! Upload a CSV or Excel file to get started, and I'll help you analyze your data.",
        metadata={'timestamp': datetime.now(timezone.utc).isoformat()}
    )
    
    session_data['messages'].append(welcome_msg.to_dict())
    sessions[session_id] = session_data  # Save updated session
    
    logger.info(f"Created new session: {session_id}")
    
    return jsonify({
        'session_id': session_id,
        'message': welcome_msg.to_dict()
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and return initial schema inspection"""
    # Log request details for debugging
    logger.info(f"Upload request received - Content-Type: {request.content_type}")
    logger.info(f"Form data keys: {list(request.form.keys())}")
    logger.info(f"Files: {list(request.files.keys())}")
    
    session_id = request.form.get('session_id')
    
    if not session_id:
        logger.error("No session_id in request")
        return jsonify({'error': 'Missing session_id'}), 400
    
    if session_id not in sessions:
        logger.error(f"Invalid session_id: {session_id}")
        logger.info(f"Available sessions: {list(sessions.keys())}")
        return jsonify({'error': 'Invalid or expired session. Please refresh the page.'}), 400
    
    if 'file' not in request.files:
        logger.error("No file in request.files")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        logger.error("Empty filename")
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'File type not supported. Please upload CSV or Excel files.'}), 400
    
    try:
        # Save and process file
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        file.save(file_path)
        
        logger.info(f"File saved: {file_path}")
        
        # Load and inspect schema
        df = file_handler.load_file(file_path)
        schema_info = convert_numpy_types(schema_inspector.inspect(df, filename))
        
        # Phase 2: Preprocess the data
        cleaned_df, preprocessing_manifest = preprocessor.preprocess(df, filename)
        preprocessing_manifest = convert_numpy_types(preprocessing_manifest)
        
        # Save cleaned data
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{file_id}_{filename}")
        if filename.endswith('.csv'):
            cleaned_df.to_csv(processed_path, index=False)
        else:
            cleaned_df.to_excel(processed_path, index=False)
        
        # Load session and update it
        session_data = sessions[session_id]
        session_data['dataset'] = {
            'file_id': file_id,
            'filename': filename,
            'file_path': file_path,
            'processed_path': processed_path,
            'schema': schema_info,
            'preprocessing_manifest': preprocessing_manifest
        }
        
        # Create upload confirmation message
        upload_msg = ChatMessage(
            type=MessageType.SYSTEM,
            content=f"✅ **File uploaded successfully!**\n\n**{filename}** loaded with {schema_info['row_count']:,} rows and {schema_info['column_count']} columns.",
            metadata={
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'file_info': {
                    'name': filename,
                    'rows': schema_info['row_count'],
                    'columns': schema_info['column_count'],
                    'schema_summary': schema_info['columns'][:5]
                }
            }
        )
        session_data['messages'].append(upload_msg.to_dict())
        
        # Create health report message
        health_report = preprocessor.generate_health_report(preprocessing_manifest)
        health_msg = ChatMessage(
            type=MessageType.SYSTEM,
            content=health_report,
            metadata={
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': 'health_report',
                'manifest': preprocessing_manifest
            }
        )
        session_data['messages'].append(health_msg.to_dict())
        
        # Save updated session
        sessions[session_id] = session_data
        
        logger.info(f"Upload successful for session {session_id}")
        
        return jsonify({
            'success': True,
            'messages': [upload_msg.to_dict(), health_msg.to_dict()],
            'dataset_id': file_id
        })
        
    except (pd.errors.EmptyDataError, pd.errors.ParserError, MemoryError, Exception) as e:
        error_msg = handle_error(session_id, e, "file_upload")
        status_code = 413 if isinstance(e, MemoryError) else 400
        return jsonify({'success': False, 'message': error_msg}), status_code


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle user chat messages"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
            
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()
        
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid or expired session. Please refresh the page.'}), 400
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
    except Exception as e:
        logger.error(f"Error parsing chat request: {e}")
        return jsonify({'error': 'Invalid request format'}), 400
    
    # Store user message
    user_msg = ChatMessage(
        type=MessageType.USER,
        content=user_message,
        metadata={'timestamp': datetime.now(timezone.utc).isoformat()}
    )
    save_message_to_session(session_id, user_msg)
    
    # Check if dataset is loaded
    session_data = sessions[session_id]
    if not session_data.get('dataset'):
        response_msg = ChatMessage(
            type=MessageType.SYSTEM,
            content="Please upload a dataset first before asking questions.",
            metadata={'timestamp': datetime.now(timezone.utc).isoformat()}
        )
        save_message_to_session(session_id, response_msg)
        return jsonify({'success': True, 'message': response_msg.to_dict()})
    
    # Phase 3: Process the query with AI
    try:
        # Load processed data
        dataset_info = session_data['dataset']
        processed_path = dataset_info['processed_path']
        df = file_handler.load_file(processed_path)
        
        # Get conversation history for context
        conversation_history = session_data['messages']
        
        # Phase 3: AI-powered intent detection with full dataset context
        logger.info("🧠 Phase 3: Detecting intent with AI...")
        intent_result = intent_detector.detect_intent(
            user_message, 
            df,
            conversation_history
        )
        logger.info(f"✅ Intent detected: {intent_result.get('query_type', 'unknown')}")
        
        # Show AI's understanding
        if intent_result.get('explanation'):
            logger.info(f"🤖 AI understood: {intent_result['explanation']}")
        
        # Check if clarification needed (AI should rarely need this)
        if intent_result['clarifications_needed']:
            # AI determined it truly needs clarification
            clarification_msg = "\n".join([
                clarif if isinstance(clarif, str) else clarif.get('message', str(clarif))
                for clarif in intent_result['clarifications_needed']
            ])
            
            response_msg = ChatMessage(
                type=MessageType.CLARIFICATION,
                content=clarification_msg,
                metadata={
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'intent_result': intent_result
                }
            )
            save_message_to_session(session_id, response_msg)
            return jsonify({'success': True, 'message': response_msg.to_dict()})
        
        # Phase 3.5: Query Refinement - Make queries more analytically useful
        logger.info("🎯 Phase 3.5: Refining query for better insights...")
        dataset_context_brief = f"{len(df)} rows, {len(df.columns)} columns: {', '.join(df.columns.tolist()[:5])}"
        refinement = query_refiner.refine_query(
            user_message, 
            intent_result, 
            dataset_context_brief,
            conversation_history  # Pass conversation history for context
        )
        
        if refinement.get('refinement_applied'):
            logger.info(f"✨ Query refined: {refinement.get('reasoning')}")
            refined_display = query_refiner.format_refinement_for_display(refinement)
            if refined_display:
                refinement_msg = ChatMessage(
                    type=MessageType.SYSTEM,
                    content=refined_display,
                    metadata={'timestamp': datetime.now(timezone.utc).isoformat()}
                )
                save_message_to_session(session_id, refinement_msg)
            
            # Use refined query for planning and code generation
            query_to_use = refinement.get('refined_query', user_message)
        else:
            logger.info("✓ Query is already optimal, no refinement needed")
            query_to_use = user_message
        
        # Phase 4: Create execution plan
        logger.info("📋 Phase 4: Creating execution plan...")
        dataset_summary = {
            'row_count': len(df),
            'columns': df.columns.tolist()
        }
        execution_plan = query_planner.create_plan(
            query_to_use,  # Use refined query
            intent_result,
            dataset_summary
        )
        
        # Show plan if complex
        if execution_plan.get('needs_planning'):
            plan_display = query_planner.format_plan_for_display(execution_plan)
            plan_msg = ChatMessage(
                type=MessageType.SYSTEM,
                content=plan_display,
                metadata={
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'plan': execution_plan,
                    'type': 'execution_plan'
                }
            )
            save_message_to_session(session_id, plan_msg)
        
        # Phase 5-7: Code generation, validation, and execution loop
        df_dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        generated_code = None
        validation_result = None
        execution_result = None
        
        for attempt in range(retry_manager.max_retries):
            logger.info(f"🔄 Attempt {attempt + 1}/{retry_manager.max_retries}")
            
            # Phase 5: Generate code
            logger.info("📝 Phase 5: Generating code...")
            code_result = code_generator.generate_code(
                query_to_use,  # Use refined query
                intent_result,
                execution_plan,
                df.columns.tolist(),
                df_dtypes
            )
            generated_code = code_result
            logger.info(f"✅ Code generated ({len(code_result['code'])} chars)")
            logger.info(f"📝 Generated code:\n{code_result['code']}")
            
            # Show generated code
            if attempt == 0:  # Only show code on first attempt
                code_display = code_generator.format_code_for_display(code_result)
                code_msg = ChatMessage(
                    type=MessageType.SYSTEM,
                    content=code_display,
                    metadata={
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'code': code_result['code'],
                        'type': 'generated_code'
                    }
                )
                save_message_to_session(session_id, code_msg)
            
            # Phase 6: Validate code
            logger.info("🔍 Phase 6: Validating code...")
            validation_result = code_validator.validate(
                code_result['code'],
                df.columns.tolist()
            )
            logger.info(f"Validation: {'✅ PASSED' if validation_result['valid'] else '❌ FAILED'}")
            
            # Debug: Log validation errors
            if not validation_result['valid']:
                logger.info(f"🔍 Validation errors: {validation_result.get('errors', [])}")
                logger.info(f"🔍 Validation warnings: {validation_result.get('warnings', [])}")
            
            if not validation_result['valid']:
                # Show validation errors
                validation_display = code_validator.format_validation_for_display(validation_result)
                validation_msg = ChatMessage(
                    type=MessageType.ERROR,
                    content=validation_display,
                    metadata={
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'validation': validation_result,
                        'type': 'validation_error'
                    }
                )
                save_message_to_session(session_id, validation_msg)
                
                # Check if should retry
                should_retry, feedback = retry_manager.should_retry(attempt + 1, validation_result)
                if should_retry:
                    retry_display = retry_manager.format_retry_info(attempt + 2, feedback)
                    retry_msg = ChatMessage(
                        type=MessageType.SYSTEM,
                        content=retry_display,
                        metadata={'timestamp': datetime.now(timezone.utc).isoformat()}
                    )
                    save_message_to_session(session_id, retry_msg)
                    continue  # Retry
                else:
                    # Max retries reached
                    error_msg = ChatMessage(
                        type=MessageType.ERROR,
                        content="Failed to generate valid code after multiple attempts.",
                        metadata={'timestamp': datetime.now(timezone.utc).isoformat()}
                    )
                    save_message_to_session(session_id, error_msg)
                    return jsonify({'success': True, 'message': error_msg.to_dict()})
            
            # Phase 7: Execute code safely
            logger.info("⚡ Phase 7: Executing code in sandbox...")
            execution_result = safe_executor.execute(code_result['code'], df)
            logger.info(f"Execution: {'✅ SUCCESS' if execution_result['success'] else '❌ FAILED'}")
            
            if execution_result['success']:
                # Success! Generate insights and answer
                logger.info(f"📊 Phase 8: Generating insights and answer...")
                
                messages_to_send = []
                
                # Phase 8a: Generate insights (charts, key findings)
                # Pass requested chart type from query refinement
                requested_chart = refinement.get('requested_chart_type') if refinement else None
                insights = insight_generator.generate_insights(
                    execution_result['result'],
                    user_message,
                    execution_result['execution_time'],
                    requested_chart_type=requested_chart
                )
                
                if insights['narrative'] or insights['key_findings']:
                    insights_display = insight_generator.format_insights_for_display(insights)
                    insights_msg = ChatMessage(
                        type=MessageType.SYSTEM,
                        content=insights_display,
                        metadata={
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'insights': insights,
                            'generated_code': code_result['code'],  # Include code for "Show Code" button
                            'type': 'insights'
                        }
                    )
                    save_message_to_session(session_id, insights_msg)
                    messages_to_send.append(insights_msg.to_dict())
                
                # Phase 8b: Synthesize plain-language answer
                try:
                    query_context = {
                        'refined_query': query_to_use if query_to_use != user_message else None,
                        'execution_time': execution_result['execution_time']
                    }
                    answer = answer_synthesizer.synthesize_answer(
                        user_message,
                        execution_result['result'],
                        query_context
                    )
                    
                    if answer:
                        answer_display = answer_synthesizer.format_answer_for_display(answer)
                        answer_msg = ChatMessage(
                            type=MessageType.SYSTEM,
                            content=answer_display,
                            metadata={
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'type': 'answer'
                            }
                        )
                        save_message_to_session(session_id, answer_msg)
                        messages_to_send.append(answer_msg.to_dict())
                        logger.info("✅ Answer synthesized successfully")
                    else:
                        logger.warning("⚠️ Answer synthesis returned None")
                except Exception as e:
                    logger.error(f"❌ Answer synthesis failed: {str(e)}")
                    # Continue without answer - insights are still useful
                
                logger.info("✅ Insights generation complete")
                
                # Return all messages
                if messages_to_send:
                    return jsonify({
                        'success': True,
                        'message': messages_to_send[0],
                        'additional_messages': messages_to_send[1:] if len(messages_to_send) > 1 else []
                    })
                else:
                    # Fallback: show raw result
                    result_display = safe_executor.format_result_for_display(
                        execution_result,
                        execution_result['result']
                    )
                    result_msg = ChatMessage(
                        type=MessageType.RESULT,
                        content=result_display,
                        metadata={
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'type': 'execution_result'
                        }
                    )
                    save_message_to_session(session_id, result_msg)
                    return jsonify({
                        'success': True,
                        'message': result_msg.to_dict()
                    })
            else:
                # Execution failed
                logger.warning(f"⚠️ Execution failed: {execution_result.get('error', 'Unknown error')}")
                error_display = safe_executor.format_result_for_display(execution_result, None)
                error_msg = ChatMessage(
                    type=MessageType.ERROR,
                    content=error_display,
                    metadata={
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'error': execution_result.get('error'),
                        'type': 'execution_error'
                    }
                )
                save_message_to_session(session_id, error_msg)
                
                # Try regenerating code with error feedback
                if attempt < retry_manager.max_retries - 1:
                    logger.info(f"🔄 Retrying... (attempt {attempt + 2}/{retry_manager.max_retries})")
                    retry_msg = ChatMessage(
                        type=MessageType.SYSTEM,
                        content=f"🔄 Regenerating code (Attempt {attempt + 2}/{retry_manager.max_retries})",
                        metadata={'timestamp': datetime.now(timezone.utc).isoformat()}
                    )
                    save_message_to_session(session_id, retry_msg)
                    continue
                else:
                    return jsonify({'success': True, 'message': error_msg.to_dict()})
        
        # If we get here, all retries failed
        final_error_msg = ChatMessage(
            type=MessageType.ERROR,
            content="Unable to execute query after multiple attempts.",
            metadata={'timestamp': datetime.now(timezone.utc).isoformat()}
        )
        save_message_to_session(session_id, final_error_msg)
        return jsonify({'success': True, 'message': final_error_msg.to_dict()})
    
    except (KeyError, FileNotFoundError, Exception) as e:
        error_msg = handle_error(session_id, e, "chat_query")
        return jsonify({'success': True, 'message': error_msg})


@app.route('/api/session/<session_id>/messages', methods=['GET'])
def get_messages(session_id):
    """Retrieve all messages for a session"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'session_id': session_id,
        'messages': sessions[session_id]['messages']
    })


@app.route('/api/session/<session_id>/preview', methods=['GET'])
def preview_data(session_id):
    """Preview the preprocessed dataset"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = sessions[session_id]
    if not session_data.get('dataset'):
        return jsonify({'error': 'No dataset loaded'}), 400
    
    try:
        # Load processed data
        processed_path = session_data['dataset']['processed_path']
        df = file_handler.load_file(processed_path)
        
        # Get preview (first 100 rows)
        preview_df = df.head(100)
        
        # Convert datetime columns to strings for JSON serialization
        for col in preview_df.columns:
            if pd.api.types.is_datetime64_any_dtype(preview_df[col]):
                preview_df[col] = preview_df[col].astype(str)
        
        # Convert to records format for JSON
        preview_data = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'preview_rows': len(preview_df),
            'columns': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'data': convert_numpy_types(preview_df.to_dict('records')),
            'preprocessing_applied': session_data['dataset']['preprocessing_manifest']['steps_applied']
        }
        
        return jsonify(preview_data)
        
    except Exception as e:
        logger.error(f"Preview failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'api_version': 'v1',
        'features': {
            'chat_interface': True,
            'rest_api': True,
            'code_generation': True,
            'visualization': True,
            'colorful_charts': True
        },
        'endpoints': {
            'chat': '/api/chat',
            'rest_api': '/api/v1/',
            'analyze': '/api/v1/analyze',
            'query': '/api/v1/query',
            'validate_code': '/api/v1/code/validate',
            'execute_code': '/api/v1/code/execute',
            'status': '/api/v1/status/<session_id>'
        }
    })


if __name__ == '__main__':
    print("🚀 NLytics Backend starting...")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📁 Processed folder: {app.config['PROCESSED_FOLDER']}")
    
    # Development server only - use Gunicorn for production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')


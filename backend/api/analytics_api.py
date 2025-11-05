"""
NLytics REST API
Comprehensive API for programmatic access to all analytics functionality
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def serialize_result(result):
    """Convert result to JSON-serializable format"""
    if isinstance(result, pd.DataFrame):
        return result.to_dict('records')
    elif isinstance(result, pd.Series):
        return result.to_dict()
    elif isinstance(result, (np.integer, np.int64, np.int32)):
        return int(result)
    elif isinstance(result, (np.floating, np.float64, np.float32)):
        return float(result)
    elif isinstance(result, np.ndarray):
        return result.tolist()
    elif isinstance(result, np.bool_):
        return bool(result)
    return result

# This will be initialized from main.py with all the service instances
api_blueprint = Blueprint('api', __name__, url_prefix='/api/v1')

# Global references to services (set from main.py)
services = {}
sessions = {}


def init_api(service_dict, session_store):
    """Initialize API with service instances and session store"""
    global services, sessions
    services = service_dict
    sessions = session_store


@api_blueprint.route('/analyze', methods=['POST'])
def analyze():
    """
    Complete analysis endpoint - Upload data and get insights in one call
    
    Request (multipart/form-data or JSON):
        - file: CSV/Excel file (if multipart)
        - data_url: URL to dataset (if JSON)
        - query: Natural language question
        - return_code: Include generated code (default: true)
        - return_visualization: Include chart config (default: true)
    
    Response:
        {
            "success": true,
            "status": "completed",
            "query": {
                "original": "highest stock",
                "refined": "top 10 stocks comparison",
                "intent": {...}
            },
            "code": {
                "generated": "df.nlargest(10, 'Close')...",
                "language": "python",
                "execution_time": 0.23
            },
            "result": {
                "data": [...],
                "row_count": 10,
                "column_count": 5
            },
            "visualization": {
                "type": "bar",
                "config": {...},
                "suitable": true
            },
            "insights": {
                "narrative": "AAPL leads with...",
                "key_findings": [...],
                "recommendations": [...]
            },
            "answer": "Based on the data, AAPL is the highest..."
        }
    """
    try:
        # Handle multipart form data or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # File upload
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            query = request.form.get('query', '')
            return_code = request.form.get('return_code', 'true').lower() == 'true'
            return_viz = request.form.get('return_visualization', 'true').lower() == 'true'
        else:
            # JSON request
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid request body'}), 400
            
            query = data.get('query', '')
            return_code = data.get('return_code', True)
            return_viz = data.get('return_visualization', True)
            
            # Handle data_url or inline data later
            return jsonify({'error': 'File upload required in current version'}), 400
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Create temporary session for this request
        session_id = f"api_{datetime.now().timestamp()}"
        
        # Upload and process file (same logic as main.py upload)
        import uuid
        from werkzeug.utils import secure_filename
        import os
        
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        upload_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, f"{file_id}_{filename}")
        file.save(file_path)
        
        df = services['file_handler'].load_file(file_path)
        
        # Preprocess
        processed_df, preprocessing_manifest = services['preprocessor'].preprocess(df, filename)
        
        # Detect intent
        intent_result = services['intent_detector'].detect_intent(
            query, 
            processed_df,
            []
        )
        
        # Refine query
        dataset_context = f"{len(processed_df)} rows, {len(processed_df.columns)} columns"
        refinement = services['query_refiner'].refine_query(query, intent_result, dataset_context)
        query_to_use = refinement.get('refined_query', query) if refinement.get('refinement_applied') else query
        
        # Create plan
        execution_plan = services['query_planner'].create_plan(
            query_to_use,
            intent_result,
            {'row_count': len(processed_df), 'columns': processed_df.columns.tolist()}
        )
        
        # Generate and execute code
        df_dtypes = {col: str(dtype) for col, dtype in processed_df.dtypes.items()}
        code_result = services['code_generator'].generate_code(
            query_to_use,
            intent_result,
            execution_plan,
            processed_df.columns.tolist(),
            df_dtypes
        )
        
        # Validate
        validation_result = services['code_validator'].validate(
            code_result['code'],
            processed_df.columns.tolist()
        )
        
        if not validation_result['valid']:
            return jsonify({
                'error': 'Code validation failed',
                'details': validation_result.get('errors', [])
            }), 500
        
        # Execute
        execution_result = services['safe_executor'].execute(
            code_result['code'],
            processed_df
        )
        
        if not execution_result['success']:
            return jsonify({
                'error': 'Execution failed',
                'details': execution_result.get('error', 'Unknown error')
            }), 500
        
        # Generate insights
        insights = services['insight_generator'].generate_insights(
            execution_result['result'],
            query_to_use,
            execution_result.get('execution_time', 0)
        )
        
        # Synthesize answer
        query_context = {
            'refined_query': query_to_use if refinement.get('refinement_applied') else None,
            'execution_time': execution_result.get('execution_time', 0)
        }
        answer = services['answer_synthesizer'].synthesize_answer(
            query_to_use,
            execution_result['result'],
            query_context
        )
        
        # Build response
        response = {
            'success': True,
            'status': 'completed',
            'query': {
                'original': query,
                'refined': query_to_use if refinement.get('refinement_applied') else None,
                'intent': {
                    'type': intent_result.get('query_type'),
                    'explanation': intent_result.get('explanation')
                }
            },
            'result': {
                'data': serialize_result(execution_result['result']),
                'type': str(type(execution_result['result']).__name__)
            },
            'insights': {
                'narrative': insights.get('narrative', ''),
                'key_findings': insights.get('key_findings', []),
                'recommendations': insights.get('recommendations', [])
            },
            'answer': answer
        }
        
        # Optional fields
        if return_code:
            response['code'] = {
                'generated': code_result['code'],
                'language': 'python',
                'explanation': code_result.get('explanation', ''),
                'execution_time': execution_result.get('execution_time', 0)
            }
        
        if return_viz and insights.get('visualization'):
            response['visualization'] = insights['visualization']
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"API analyze error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/query', methods=['POST'])
def query_endpoint():
    """
    Query existing session
    
    Request:
        {
            "session_id": "uuid",
            "query": "show me top stocks"
        }
    
    Response: Same as /analyze
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        query = data.get('query', '')
        
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid session_id'}), 400
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Get session data
        session = sessions[session_id]
        if not session.get('dataset'):
            return jsonify({'error': 'No dataset loaded in session'}), 400
        
        # Load processed data
        processed_path = session['dataset']['processed_path']
        df = services['file_handler'].load_file(processed_path)
        
        # Run full pipeline (same as analyze)
        intent_result = services['intent_detector'].detect_intent(
            query, 
            df,
            session.get('messages', [])
        )
        
        dataset_context = f"{len(df)} rows, {len(df.columns)} columns"
        refinement = services['query_refiner'].refine_query(query, intent_result, dataset_context)
        query_to_use = refinement.get('refined_query', query) if refinement.get('refinement_applied') else query
        
        execution_plan = services['query_planner'].create_plan(
            query_to_use,
            intent_result,
            {'row_count': len(df), 'columns': df.columns.tolist()}
        )
        
        df_dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        code_result = services['code_generator'].generate_code(
            query_to_use,
            intent_result,
            execution_plan,
            df.columns.tolist(),
            df_dtypes
        )
        
        validation_result = services['code_validator'].validate(
            code_result['code'],
            df.columns.tolist()
        )
        
        if not validation_result['valid']:
            return jsonify({
                'error': 'Code validation failed',
                'details': validation_result.get('errors', [])
            }), 500
        
        execution_result = services['safe_executor'].execute(code_result['code'], df)
        
        if not execution_result['success']:
            return jsonify({
                'error': 'Execution failed',
                'details': execution_result.get('error', 'Unknown error')
            }), 500
        
        insights = services['insight_generator'].generate_insights(
            execution_result['result'],
            query_to_use,
            execution_result.get('execution_time', 0)
        )
        
        query_context = {
            'refined_query': query_to_use if refinement.get('refinement_applied') else None,
            'execution_time': execution_result.get('execution_time', 0)
        }
        answer = services['answer_synthesizer'].synthesize_answer(
            query_to_use,
            execution_result['result'],
            query_context
        )
        
        response = {
            'success': True,
            'status': 'completed',
            'session_id': session_id,
            'query': {
                'original': query,
                'refined': query_to_use if refinement.get('refinement_applied') else None,
                'intent': {
                    'type': intent_result.get('query_type'),
                    'explanation': intent_result.get('explanation')
                }
            },
            'code': {
                'generated': code_result['code'],
                'language': 'python',
                'explanation': code_result.get('explanation', ''),
                'execution_time': execution_result.get('execution_time', 0)
            },
            'result': {
                'data': serialize_result(execution_result['result']),
                'type': str(type(execution_result['result']).__name__)
            },
            'visualization': insights.get('visualization'),
            'insights': {
                'narrative': insights.get('narrative', ''),
                'key_findings': insights.get('key_findings', []),
                'recommendations': insights.get('recommendations', [])
            },
            'answer': answer
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"API query error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """
    Get session status
    
    Response:
        {
            "session_id": "uuid",
            "status": "active",
            "dataset": {
                "loaded": true,
                "filename": "data.csv",
                "rows": 1000,
                "columns": 10
            },
            "message_count": 5,
            "created_at": "2025-11-05T..."
        }
    """
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = sessions[session_id]
    
    response = {
        'session_id': session_id,
        'status': 'active',
        'dataset': None,
        'message_count': len(session.get('messages', [])),
        'created_at': session.get('created_at')
    }
    
    if session.get('dataset'):
        ds = session['dataset']
        response['dataset'] = {
            'loaded': True,
            'filename': ds.get('filename'),
            'rows': ds.get('row_count'),
            'columns': ds.get('column_count'),
            'column_names': ds.get('columns', [])
        }
    
    return jsonify(response), 200


@api_blueprint.route('/code/validate', methods=['POST'])
def validate_code():
    """
    Validate Python code without execution
    
    Request:
        {
            "code": "df.nlargest(10, 'Close')",
            "columns": ["Close", "Open", "High"]
        }
    
    Response:
        {
            "is_valid": true,
            "errors": [],
            "warnings": []
        }
    """
    try:
        data = request.get_json()
        code = data.get('code', '')
        columns = data.get('columns', [])
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        validation_result = services['code_validator'].validate(code, columns)
        
        return jsonify(validation_result), 200
        
    except Exception as e:
        logger.error(f"Code validation error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_blueprint.route('/code/execute', methods=['POST'])
def execute_code():
    """
    Execute validated code (use with caution)
    
    Request:
        {
            "session_id": "uuid",
            "code": "df.nlargest(10, 'Close')"
        }
    
    Response:
        {
            "success": true,
            "result": {...},
            "execution_time": 0.15
        }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        code = data.get('code', '')
        
        if not session_id or session_id not in sessions:
            return jsonify({'error': 'Invalid session_id'}), 400
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        session = sessions[session_id]
        if not session.get('dataset'):
            return jsonify({'error': 'No dataset loaded'}), 400
        
        # Load data
        processed_path = session['dataset']['processed_path']
        df = services['file_handler'].load_file(processed_path)
        
        # Validate first
        validation_result = services['code_validator'].validate(code, df.columns.tolist())
        if not validation_result['valid']:
            return jsonify({
                'error': 'Code validation failed',
                'details': validation_result
            }), 400
        
        # Execute
        execution_result = services['safe_executor'].execute(code, df)
        
        if not execution_result['success']:
            return jsonify({
                'success': False,
                'error': execution_result.get('error', 'Execution failed')
            }), 500
        
        return jsonify({
            'success': True,
            'result': serialize_result(execution_result['result']),
            'execution_time': execution_result.get('execution_time', 0)
        }), 200
        
    except Exception as e:
        logger.error(f"Code execution error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

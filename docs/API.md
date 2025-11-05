# NLytics REST API Documentation

## Overview

NLytics provides a comprehensive REST API for programmatic access to all analytics functionality. The API enables you to upload datasets, execute natural language queries, get generated code, visualizations, and insights.

**Base URL**: `http://localhost:5000/api/v1`

**Version**: 1.0.0

## Authentication

Currently no authentication required (add API keys in production).

## Endpoints

### 1. Complete Analysis (One-Shot)

Upload data and get complete analysis in a single request.

**Endpoint**: `POST /api/v1/analyze`

**Content-Type**: `multipart/form-data`

**Request Parameters**:
- `file` (required): CSV or Excel file
- `query` (required): Natural language question
- `return_code` (optional): Include generated code (default: true)
- `return_visualization` (optional): Include chart config (default: true)

**Example Request**:
```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "file=@stock_data.csv" \
  -F "query=highest growing stock" \
  -F "return_code=true"
```

**Response** (200 OK):
```json
{
  "success": true,
  "status": "completed",
  "query": {
    "original": "highest growing stock",
    "refined": "top 10 stocks by growth comparison",
    "intent": {
      "type": "ranking",
      "explanation": "User wants to find and compare highest performing stocks"
    }
  },
  "code": {
    "generated": "df['growth'] = ((df['Close'] - df['Open']) / df['Open']) * 100\nresult = df.nlargest(10, 'growth')[['Symbol', 'growth']].round(2)",
    "language": "python",
    "explanation": "Calculate growth rate and get top 10",
    "execution_time": 0.23
  },
  "result": {
    "data": [
      {"Symbol": "AAPL", "growth": 15.3},
      {"Symbol": "MSFT", "growth": 12.1}
    ],
    "type": "DataFrame"
  },
  "visualization": {
    "type": "bar",
    "suitable": true,
    "x_column": "Symbol",
    "y_column": "growth",
    "x_values": ["AAPL", "MSFT", "GOOGL"],
    "y_values": [15.3, 12.1, 10.5],
    "colors": ["#3b82f6", "#10b981", "#f59e0b"],
    "description": "Growth Rate (%) by Symbol",
    "y_label": "Growth Rate (%)"
  },
  "insights": {
    "narrative": "AAPL leads with growth rate of 15.3%, while MSFT follows at 12.1%.",
    "key_findings": [
      "Highest: AAPL (15.3%)",
      "Average across all: 9.2%"
    ],
    "recommendations": [
      "Export data for further analysis",
      "Compare with other time periods"
    ]
  },
  "answer": "Based on the data, AAPL is the highest growing stock with a 15.3% increase, followed by MSFT at 12.1%."
}
```

---

### 2. Session-Based Query

Execute query on existing session.

**Endpoint**: `POST /api/v1/query`

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "session_id": "abc-123",
  "query": "show average price by sector"
}
```

**Response**: Same structure as `/analyze`

**Example**:
```bash
curl -X POST http://localhost:5000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc-123", "query": "top 10 by volume"}'
```

---

### 3. Get Session Status

Check session status and dataset info.

**Endpoint**: `GET /api/v1/status/<session_id>`

**Response** (200 OK):
```json
{
  "session_id": "abc-123",
  "status": "active",
  "dataset": {
    "loaded": true,
    "filename": "stock_data.csv",
    "rows": 4348,
    "columns": 14,
    "column_names": ["Symbol", "Date", "Open", "Close", "Volume"]
  },
  "message_count": 5,
  "created_at": "2025-11-05T10:30:00Z"
}
```

**Example**:
```bash
curl http://localhost:5000/api/v1/status/abc-123
```

---

### 4. Validate Code

Validate Python code without execution.

**Endpoint**: `POST /api/v1/code/validate`

**Request Body**:
```json
{
  "code": "df.nlargest(10, 'Close')",
  "columns": ["Close", "Open", "High", "Low"]
}
```

**Response** (200 OK):
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": []
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/api/v1/code/validate \
  -H "Content-Type: application/json" \
  -d '{"code": "df.nlargest(10, \"Close\")", "columns": ["Close"]}'
```

---

### 5. Execute Code

Execute validated code on session dataset.

**Endpoint**: `POST /api/v1/code/execute`

**Request Body**:
```json
{
  "session_id": "abc-123",
  "code": "df.nlargest(10, 'Close')"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "result": [...],
  "execution_time": 0.15
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/api/v1/code/execute \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc-123", "code": "df.describe()"}'
```

---

## Visualization Configuration

When `return_visualization=true`, the API returns Plotly chart configuration (with Chart.js fallback):

### Bar Chart
```json
{
  "type": "bar",
  "suitable": true,
  "plotly": "{\"data\": [...], \"layout\": {...}}",
  "x_values": ["A", "B", "C"],
  "y_values": [10, 20, 15],
  "colors": ["#3b82f6", "#10b981", "#f59e0b"],
  "y_label": "Value"
}
```

### Scatter Plot
```json
{
  "type": "scatter",
  "suitable": true,
  "plotly": "{\"data\": [...], \"layout\": {...}}",
  "x_values": [1, 2, 3],
  "y_values": [10, 20, 15],
  "point_color": "#3b82f6"
}
```

The `plotly` field contains a JSON string with Plotly figure data for interactive charts. The `x_values`, `y_values`, and `colors` fields provide fallback data for Chart.js rendering.

## Color Palette

The API uses a professional, vibrant color palette:

```
#3b82f6  Blue
#10b981  Green
#f59e0b  Amber
#ef4444  Red
#8b5cf6  Purple
#ec4899  Pink
#14b8a6  Teal
#f97316  Orange
#6366f1  Indigo
#84cc16  Lime
#06b6d4  Cyan
#f43f5e  Rose
```

Different bars/points get different colors automatically for better visual distinction.

## Error Responses

### 400 Bad Request
```json
{
  "error": "Query is required"
}
```

### 404 Not Found
```json
{
  "error": "Session not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Execution failed",
  "details": "Column 'X' not found in dataset"
}
```

## Python Client Example

```python
import requests

# Upload and analyze
with open('data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/v1/analyze',
        files={'file': f},
        data={
            'query': 'show me top 10 stocks by volume',
            'return_code': 'true',
            'return_visualization': 'true'
        }
    )

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Code: {result['code']['generated']}")

# Visualization data
viz = result['visualization']
if viz and viz['suitable']:
    import matplotlib.pyplot as plt
    plt.bar(viz['x_values'], viz['y_values'], color=viz['colors'])
    plt.show()
```

## JavaScript Client Example

```javascript
// Fetch API
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('query', 'average price by sector');

const response = await fetch('http://localhost:5000/api/v1/analyze', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log('Answer:', data.answer);

// Render chart with Chart.js
if (data.visualization && data.visualization.suitable) {
  const viz = data.visualization;
  new Chart(ctx, {
    type: viz.type,
    data: {
      labels: viz.x_values,
      datasets: [{
        data: viz.y_values,
        backgroundColor: viz.colors
      }]
    }
  });
}
```

## Health Check

**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "api_version": "v1",
  "features": {
    "chat_interface": true,
    "rest_api": true,
    "code_generation": true,
    "visualization": true,
    "colorful_charts": true
  },
  "endpoints": {
    "analyze": "/api/v1/analyze",
    "query": "/api/v1/query",
    "validate_code": "/api/v1/code/validate",
    "execute_code": "/api/v1/code/execute",
    "status": "/api/v1/status/<session_id>"
  }
}
```

## Rate Limits

No rate limits in current version. Add rate limiting for production deployment.

## Support

For issues or questions:
- GitHub Issues: https://github.com/Tech-Genkai/NLytics/issues
- Documentation: `/docs/`

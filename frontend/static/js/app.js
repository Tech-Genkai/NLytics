/**
 * NLytics Frontend Application
 * Handles chat interface, file uploads, and message rendering
 */

class NLyticsApp {
    constructor() {
        this.sessionId = null;
        // Check if running locally (localhost, 127.0.0.1, or any development port)
        const isLocal = window.location.hostname === 'localhost' || 
                       window.location.hostname === '127.0.0.1' ||
                       window.location.hostname === '' ||
                       window.location.port === '5000';
        
        this.apiUrl = isLocal
            ? 'http://localhost:5000/api' 
            : 'https://nlytics.onrender.com/api';
        
        // DOM elements
        this.messagesList = document.getElementById('messages');
        this.chatContainer = document.querySelector('.chat-container');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.uploadBtn = document.getElementById('upload-btn');
        this.previewBtn = document.getElementById('preview-btn');
        this.fileInput = document.getElementById('file-input');
        this.loadingIndicator = document.getElementById('loading');
        this.inputHelp = document.querySelector('.input-help');
        
        this.init();
    }
    
    async init() {
        // Verify API is accessible
        try {
            console.log('Checking API health at:', `${this.apiUrl}/health`);
            const healthResponse = await fetch(`${this.apiUrl}/health`);
            if (healthResponse.ok) {
                const health = await healthResponse.json();
                console.log('API health check passed:', health.status);
            } else {
                console.warn('API health check failed:', healthResponse.status);
            }
        } catch (error) {
            console.error('API health check error:', error);
        }
        
        // Create new session
        await this.createSession();
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Send button
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send (Shift+Enter for new line)
        this.userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.userInput.addEventListener('input', () => {
            this.userInput.style.height = 'auto';
            this.userInput.style.height = this.userInput.scrollHeight + 'px';
        });
        
        // Upload button
        this.uploadBtn.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        // File selection
        this.fileInput.addEventListener('change', () => {
            if (this.fileInput.files.length > 0) {
                this.uploadFile(this.fileInput.files[0]);
            }
        });
        
        // Preview button
        this.previewBtn.addEventListener('click', () => {
            this.showDataPreview();
        });
    }
    
    async createSession() {
        try {
            console.log('Creating new session...');
            const response = await fetch(`${this.apiUrl}/session/new`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
            console.log('Session created successfully:', this.sessionId);
            
            // Display welcome message
            this.addMessage(data.message);
            
        } catch (error) {
            console.error('Failed to create session:', error);
            this.showError('Failed to connect to server. Please refresh the page.');
        }
    }
    
    async uploadFile(file) {
        if (!this.sessionId) {
            this.showError('No active session. Please refresh the page.');
            return;
        }
        
        console.log('Uploading file:', file.name, 'Session ID:', this.sessionId);
        
        // Show loading
        this.showLoading('Uploading and analyzing file...');
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', this.sessionId);
        
        console.log('FormData contents:', {
            file: file.name,
            session_id: this.sessionId,
            size: file.size,
            type: file.type
        });
        
        try {
            console.log('Sending request to:', `${this.apiUrl}/upload`);
            const response = await fetch(`${this.apiUrl}/upload`, {
                method: 'POST',
                body: formData
            });
            
            console.log('Response status:', response.status, response.statusText);
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                // Add all messages (upload confirmation + health report)
                if (data.messages && Array.isArray(data.messages)) {
                    data.messages.forEach(msg => this.addMessage(msg));
                } else if (data.message) {
                    this.addMessage(data.message);
                }
                this.enableInput();
                this.inputHelp.textContent = 'Ask questions about your data...';
                // Show preview button
                this.previewBtn.style.display = 'block';
            } else {
                console.error('Upload failed:', data);
                if (data.message) {
                    this.addMessage(data.message);
                } else if (data.error) {
                    this.showError(data.error);
                } else {
                    this.showError('Upload failed. Please try again.');
                }
            }
            
        } catch (error) {
            console.error('Upload failed:', error);
            this.showError(`Failed to upload file: ${error.message}. Please try again.`);
        } finally {
            this.hideLoading();
            this.fileInput.value = ''; // Reset file input
        }
    }
    
    async sendMessage() {
        const message = this.userInput.value.trim();
        
        if (!message) return;
        
        // Display user message immediately
        this.addMessage({
            type: 'user',
            content: message,
            timestamp: new Date().toISOString()
        });
        
        // Clear input
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        
        // Show loading
        this.showLoading('Thinking...');
        
        try {
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Add main message
                this.addMessage(data.message);
                
                // Add any additional messages (e.g., insights)
                if (data.additional_messages && Array.isArray(data.additional_messages)) {
                    data.additional_messages.forEach(msg => this.addMessage(msg));
                }
            } else {
                this.showError(data.error || 'Failed to process message');
            }
            
        } catch (error) {
            console.error('Send message failed:', error);
            this.showError('Failed to send message. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    addMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${message.type}`;
        
        // Format timestamp
        let timestamp = 'Now';
        if (message.timestamp) {
            try {
                const date = new Date(message.timestamp);
                if (!isNaN(date.getTime())) {
                    timestamp = date.toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                }
            } catch (e) {
                timestamp = 'Now';
            }
        }
        
        // Render based on message type
        if (message.type === 'user') {
            messageEl.innerHTML = `
                <div class="message-content">
                    <div class="message-text">${this.escapeHtml(message.content)}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
        } else {
            // System, error, or result messages (with markdown support)
            const contentHtml = this.formatContent(message.content);
            const metadataHtml = this.renderMetadata(message.metadata);
            const visualizationHtml = this.renderVisualization(message.metadata);
            const codeButtonHtml = this.renderCodeButton(message.metadata);
            
            messageEl.innerHTML = `
                <div class="message-content">
                    <div class="message-text">${contentHtml}</div>
                    ${metadataHtml}
                    ${visualizationHtml}
                    ${codeButtonHtml}
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
            
            // Initialize charts after DOM insertion
            if (visualizationHtml) {
                this.messagesList.appendChild(messageEl);
                this.initializeChart(messageEl, message.metadata);
                // Don't scroll here - let initializeChart handle it after render
                return;
            }
        }
        
        this.messagesList.appendChild(messageEl);
        this.scrollToBottom();
    }
    
    formatContent(content) {
        // Use marked.js for markdown if available
        if (typeof marked !== 'undefined') {
            // Configure marked to preserve emojis and special characters
            marked.setOptions({
                breaks: true,
                gfm: true,
                sanitize: false,
                smartypants: false
            });
            return marked.parse(content);
        }
        
        // Fallback: Simple markdown formatting (don't escape HTML to preserve emojis)
        let formatted = content;
        
        // Code blocks
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang || 'python'}">${code}</code></pre>`;
        });
        
        // Inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Bold
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Headers
        formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        
        // Tables (markdown tables)
        formatted = this.formatTables(formatted);
        
        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }
    
    formatTables(content) {
        // Basic markdown table parser
        const tableRegex = /\|(.+)\|\n\|[-:\s|]+\|\n((?:\|.+\|\n?)+)/g;
        return content.replace(tableRegex, (match, header, rows) => {
            const headers = header.split('|').map(h => h.trim()).filter(h => h);
            const rowData = rows.trim().split('\n').map(row => 
                row.split('|').map(cell => cell.trim()).filter(cell => cell)
            );
            
            let tableHtml = '<table class="data-table"><thead><tr>';
            headers.forEach(h => tableHtml += `<th>${h}</th>`);
            tableHtml += '</tr></thead><tbody>';
            rowData.forEach(row => {
                tableHtml += '<tr>';
                row.forEach(cell => tableHtml += `<td>${cell}</td>`);
                tableHtml += '</tr>';
            });
            tableHtml += '</tbody></table>';
            return tableHtml;
        });
    }
    
    renderMetadata(metadata) {
        if (!metadata) return '';
        
        let html = '';
        
        // File info
        if (metadata.file_info) {
            const fileInfo = metadata.file_info;
            html += `
                <div class="file-info">
                    <div class="info-item">📄 <strong>${fileInfo.rows.toLocaleString()}</strong> rows</div>
                    <div class="info-item">📊 <strong>${fileInfo.columns}</strong> columns</div>
                </div>
            `;
        }
        
        // Code display
        if (metadata.code && metadata.type === 'generated_code') {
            html += `
                <div class="code-block">
                    <div class="code-header">
                        <span>🐍 Generated Python Code</span>
                        <button class="copy-btn" onclick="navigator.clipboard.writeText(this.dataset.code)" data-code="${this.escapeHtml(metadata.code)}">📋 Copy</button>
                    </div>
                    <pre><code class="language-python">${this.escapeHtml(metadata.code)}</code></pre>
                </div>
            `;
        }
        
        return html;
    }
    
    renderCodeButton(metadata) {
        // If there's insight metadata with generated code, show a "Show Code" button
        if (metadata && metadata.insights && metadata.generated_code) {
            const code = metadata.generated_code;
            const codeId = `code-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            return `
                <div class="code-toggle-wrapper">
                    <button class="btn-show-code" onclick="window.nlytics.toggleCode('${codeId}')">
                        <span class="code-icon">🐍</span> Show Code
                    </button>
                    <div id="${codeId}" class="code-block code-hidden">
                        <div class="code-header">
                            <span>Generated Python Code</span>
                            <button class="copy-btn" onclick="navigator.clipboard.writeText(this.dataset.code)" data-code="${this.escapeHtml(code)}">📋 Copy</button>
                        </div>
                        <pre><code class="language-python">${this.escapeHtml(code)}</code></pre>
                    </div>
                </div>
            `;
        }
        return '';
    }
    
    toggleCode(codeId) {
        const codeBlock = document.getElementById(codeId);
        const button = codeBlock.previousElementSibling;
        
        if (codeBlock.classList.contains('code-hidden')) {
            codeBlock.classList.remove('code-hidden');
            codeBlock.classList.add('code-visible');
            button.innerHTML = '<span class="code-icon">🐍</span> Hide Code';
        } else {
            codeBlock.classList.remove('code-visible');
            codeBlock.classList.add('code-hidden');
            button.innerHTML = '<span class="code-icon">🐍</span> Show Code';
        }
    }
    
    renderVisualization(metadata) {
        if (!metadata || !metadata.insights || !metadata.insights.visualization) {
            return '';
        }
        
        const viz = metadata.insights.visualization;
        if (!viz.suitable || !viz.type) return '';
        
        // Generate unique ID for chart
        const chartId = `chart-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Use div if Plotly data available, canvas for Chart.js
        const chartElement = viz.plotly ? 'div' : 'canvas';
        
        return `
            <div class="visualization-container">
                <${chartElement} id="${chartId}" data-chart-config='${JSON.stringify(viz)}'></${chartElement}>
            </div>
        `;
    }
    
    initializeChart(messageEl, metadata) {
        if (!metadata || !metadata.insights || !metadata.insights.visualization) return;
        
        // Look for either canvas or div with chart config
        const chartElement = messageEl.querySelector('[data-chart-config]');
        if (!chartElement) {
            console.warn('Chart element not found');
            return;
        }
        
        const viz = JSON.parse(chartElement.dataset.chartConfig);
        console.log('Initializing chart:', viz.type, 'Has Plotly data:', !!viz.plotly);
        
        // Try Plotly first if available
        if (viz.plotly && typeof Plotly !== 'undefined') {
            try {
                console.log('Attempting Plotly render...');
                const plotlyData = JSON.parse(viz.plotly);
                console.log('Plotly data parsed:', plotlyData);
                
                // Ensure element is a div for Plotly
                let plotlyDiv = chartElement;
                if (chartElement.tagName === 'CANVAS') {
                    console.log('Converting canvas to div for Plotly');
                    plotlyDiv = document.createElement('div');
                    plotlyDiv.id = chartElement.id;
                    chartElement.parentNode.replaceChild(plotlyDiv, chartElement);
                }
                
                plotlyDiv.style.width = '100%';
                plotlyDiv.style.height = '450px';
                
                console.log('Calling Plotly.newPlot on:', plotlyDiv.id);
                Plotly.newPlot(plotlyDiv.id, plotlyData.data, plotlyData.layout, {
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false
                }).then(() => {
                    console.log('✅ Plotly chart rendered successfully');
                    setTimeout(() => this.scrollToBottom(), 200);
                    setTimeout(() => this.scrollToBottom(), 500);
                }).catch(err => {
                    console.error('❌ Plotly.newPlot failed:', err);
                });
                
                return;
            } catch (e) {
                console.error('❌ Plotly rendering failed, falling back to Chart.js:', e);
            }
        } else {
            if (!viz.plotly) console.log('No Plotly data in viz object');
            if (typeof Plotly === 'undefined') console.warn('Plotly library not loaded');
        }
        
        // Fallback to Chart.js - need canvas element
        let canvas = chartElement;
        if (chartElement.tagName === 'DIV') {
            // Convert div to canvas for Chart.js
            canvas = document.createElement('canvas');
            canvas.id = chartElement.id;
            canvas.dataset.chartConfig = chartElement.dataset.chartConfig;
            chartElement.parentNode.replaceChild(canvas, chartElement);
        }
        
        if (!canvas || canvas.tagName !== 'CANVAS') {
            console.warn('Chart.js requires canvas element');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        const chartData = this.prepareChartData(viz, metadata);
        
        if (chartData && typeof Chart !== 'undefined') {
            // Different options for different chart types
            let chartOptions = {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: viz.type === 'pie' || viz.type === 'doughnut' || viz.type === 'line',
                        position: 'right'
                    },
                    title: {
                        display: !!viz.description,
                        text: viz.description || '',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    }
                }
            };
            
            // Add scales only for charts that need them (not pie/doughnut)
            if (viz.type !== 'pie' && viz.type !== 'doughnut' && viz.type !== 'box') {
                chartOptions.scales = {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: !!viz.y_label,
                            text: viz.y_label || ''
                        }
                    },
                    x: {
                        title: {
                            display: !!viz.x_column,
                            text: viz.x_column || ''
                        }
                    }
                };
            }
            
            new Chart(ctx, {
                type: viz.type === 'pie' ? 'doughnut' : viz.type,  // Use doughnut for pie in Chart.js
                data: chartData,
                options: chartOptions
            });
            
            setTimeout(() => this.scrollToBottom(), 200);
            setTimeout(() => this.scrollToBottom(), 500);
        }
    }
    
    prepareChartData(viz, metadata) {
        // Use actual data from backend visualization config
        
        if (viz.type === 'bar') {
            // Use colors from backend if provided, otherwise generate colorful palette
            const colors = viz.colors || this.generateColorPalette(viz.y_values?.length || 0);
            const borderColors = colors.map(c => this.adjustColorOpacity(c, 1.0));
            const bgColors = colors.map(c => this.adjustColorOpacity(c, 0.8));
            
            return {
                labels: viz.x_values || [],
                datasets: [{
                    label: viz.y_label || 'Values',
                    data: viz.y_values || [],
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 6
                }]
            };
        }
        
        if (viz.type === 'pie' || viz.type === 'doughnut') {
            // Chart.js fallback for pie/donut charts
            const colors = viz.colors || this.generateColorPalette(viz.values?.length || 0);
            const borderColors = colors.map(c => '#ffffff');
            
            return {
                labels: viz.labels || [],
                datasets: [{
                    label: viz.description || 'Distribution',
                    data: viz.values || [],
                    backgroundColor: colors,
                    borderColor: borderColors,
                    borderWidth: 2
                }]
            };
        }
        
        if (viz.type === 'scatter') {
            const points = (viz.x_values || []).map((x, i) => ({
                x: x,
                y: (viz.y_values || [])[i]
            }));
            
            const pointColor = viz.point_color || '#3b82f6';
            
            return {
                datasets: [{
                    label: viz.y_label || 'Data Points',
                    data: points,
                    backgroundColor: this.adjustColorOpacity(pointColor, 0.6),
                    borderColor: pointColor,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            };
        }
        
        if (viz.type === 'line') {
            const lineColor = viz.line_color || '#3b82f6';
            
            return {
                labels: viz.x_values || [],
                datasets: [{
                    label: viz.y_label || 'Trend',
                    data: viz.y_values || [],
                    borderColor: lineColor,
                    backgroundColor: this.adjustColorOpacity(lineColor, 0.1),
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: lineColor,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            };
        }
        
        // Box plots not supported in Chart.js - Plotly only
        if (viz.type === 'box') {
            console.warn('Box plots require Plotly - Chart.js fallback not available');
            return null;
        }
        
        return null;
    }
    
    generateColorPalette(count) {
        // Professional, vibrant color palette matching backend
        const baseColors = [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
            '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
            '#6366f1', '#84cc16', '#06b6d4', '#f43f5e'
        ];
        
        const colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(baseColors[i % baseColors.length]);
        }
        return colors;
    }
    
    adjustColorOpacity(hexColor, opacity) {
        // Convert hex to rgba with specified opacity
        const hex = hexColor.replace('#', '');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    
    showLoading(text = 'Processing...') {
        this.loadingIndicator.querySelector('.loading-text').textContent = text;
        this.loadingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }
    
    hideLoading() {
        this.loadingIndicator.style.display = 'none';
    }
    
    enableInput() {
        this.userInput.disabled = false;
        this.sendBtn.disabled = false;
        this.userInput.focus();
    }
    
    showError(message) {
        this.addMessage({
            type: 'error',
            content: message,
            timestamp: new Date().toISOString()
        });
    }
    
    async showDataPreview() {
        if (!this.sessionId) {
            this.showError('No active session');
            return;
        }
        
        this.showLoading('Loading data preview...');
        
        try {
            const response = await fetch(`${this.apiUrl}/session/${this.sessionId}/preview`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Create preview message
            const previewContent = this.formatDataPreview(data);
            
            this.addMessage({
                type: 'system',
                content: previewContent,
                metadata: {
                    timestamp: new Date().toISOString(),
                    type: 'data_preview',
                    preview_data: data
                }
            });
            
        } catch (error) {
            console.error('Preview failed:', error);
            this.showError(`Failed to load preview: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    formatDataPreview(data) {
        let html = `### &#128203; Data Preview (Preprocessed)\n\n`;
        html += `**Total Rows:** ${data.total_rows.toLocaleString()} | **Columns:** ${data.total_columns}\n`;
        html += `**Showing:** First 20 rows\n\n`;
        
        if (data.preprocessing_applied && data.preprocessing_applied.length > 0) {
            html += `**Preprocessing Applied:**\n`;
            data.preprocessing_applied.forEach(step => {
                html += `- ${step.replace(/_/g, ' ')}\n`;
            });
            html += '\n';
        }
        
        // Create table
        html += '<div style="overflow-x: auto; max-height: 400px; margin-top: 10px;">\n';
        html += '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">\n';
        
        // Header
        html += '<thead style="position: sticky; top: 0; background: #2d3748; color: white;">\n<tr>\n';
        data.columns.forEach(col => {
            const dtype = data.dtypes[col] || '';
            html += `<th style="border: 1px solid #4a5568; padding: 8px; text-align: left; white-space: nowrap;">${col}<br/><span style="font-size: 10px; color: #a0aec0;">${dtype}</span></th>\n`;
        });
        html += '</tr>\n</thead>\n';
        
        // Body - first 20 rows for display
        html += '<tbody>\n';
        const displayRows = data.data.slice(0, 20);
        displayRows.forEach((row, idx) => {
            const bgColor = idx % 2 === 0 ? '#f7fafc' : '#ffffff';
            html += `<tr style="background: ${bgColor};">\n`;
            data.columns.forEach(col => {
                let value = row[col];
                if (value === null || value === undefined) {
                    value = '<span style="color: #cbd5e0;">null</span>';
                } else if (typeof value === 'number') {
                    value = value.toLocaleString();
                } else if (typeof value === 'string' && value.length > 50) {
                    value = value.substring(0, 50) + '...';
                }
                html += `<td style="border: 1px solid #e2e8f0; padding: 6px; white-space: nowrap; color: #1a202c;">${value}</td>\n`;
            });
            html += '</tr>\n';
        });
        html += '</tbody>\n';
        html += '</table>\n</div>\n';
        
        return html;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    scrollToBottom() {
        if (this.chatContainer) {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new NLyticsApp();
    // Expose app instance globally for onclick handlers
    window.nlytics = app;
});

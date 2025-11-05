/**
 * NLytics Frontend Application
 * Handles chat interface, file uploads, and message rendering
 */

class NLyticsApp {
    constructor() {
        this.sessionId = null;
        this.apiUrl = 'http://localhost:5000/api';
        
        // DOM elements
        this.messagesList = document.getElementById('messages');
        this.chatContainer = document.querySelector('.chat-container');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.uploadBtn = document.getElementById('upload-btn');
        this.fileInput = document.getElementById('file-input');
        this.loadingIndicator = document.getElementById('loading');
        this.inputHelp = document.querySelector('.input-help');
        
        this.init();
    }
    
    async init() {
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
    }
    
    async createSession() {
        try {
            const response = await fetch(`${this.apiUrl}/session/new`, {
                method: 'POST'
            });
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
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
        
        // Show loading
        this.showLoading('Uploading and analyzing file...');
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', this.sessionId);
        
        try {
            const response = await fetch(`${this.apiUrl}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Add all messages (upload confirmation + health report)
                if (data.messages && Array.isArray(data.messages)) {
                    data.messages.forEach(msg => this.addMessage(msg));
                } else if (data.message) {
                    this.addMessage(data.message);
                }
                this.enableInput();
                this.inputHelp.textContent = 'Ask questions about your data...';
            } else {
                if (data.message) {
                    this.addMessage(data.message);
                }
            }
            
        } catch (error) {
            console.error('Upload failed:', error);
            this.showError('Failed to upload file. Please try again.');
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
        const timestamp = new Date(message.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
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
            
            messageEl.innerHTML = `
                <div class="message-content">
                    <div class="message-text">${contentHtml}</div>
                    ${metadataHtml}
                    ${visualizationHtml}
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
            return marked.parse(content);
        }
        
        // Fallback: Simple markdown formatting
        let formatted = this.escapeHtml(content);
        
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
            new Chart(ctx, {
                type: viz.type,
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false  // Hide legend since all bars have same label
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
                    },
                    scales: {
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
                    }
                }
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
    new NLyticsApp();
});

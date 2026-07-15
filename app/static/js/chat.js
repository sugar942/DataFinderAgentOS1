/**
 * Chat Interface — WebSocket streaming, @employee dispatch, conversation CRUD
 */
(function () {
    'use strict';

    let ws = null;
    let currentConvId = null;
    let currentModelId = null;
    let currentStreamBubble = null;
    let currentStreamContent = '';
    let isStreaming = false;
    let employees = [];
    let models = [];

    const dom = {
        convList: null,
        messages: null,
        textarea: null,
        sendBtn: null,
        newChatBtn: null,
        modelSelect: null,
        mentionDropdown: null,
        currentModelBadge: null,
        logoutBtn: null,
        usernameSpan: null,
        menuToggle: null,
        sidebar: null,
    };

    function $(sel) { return document.querySelector(sel); }
    function $$(sel) { return document.querySelectorAll(sel); }

    function cacheDom() {
        dom.convList = $('#convList');
        dom.messages = $('#chatMessages');
        dom.textarea = $('#chatInput');
        dom.sendBtn = $('#sendBtn');
        dom.newChatBtn = $('#newChatBtn');
        dom.modelSelect = $('#modelSelect');
        dom.mentionDropdown = $('#mentionDropdown');
        dom.currentModelBadge = $('#currentModelBadge');
        dom.logoutBtn = $('#logoutBtn');
        dom.usernameSpan = $('#chatUsername');
        dom.menuToggle = $('#menuToggle');
        dom.sidebar = $('.chat-sidebar');
    }

    // ========== WebSocket ==========
    function connectWS() {
        var proto = location.protocol === 'https:' ? 'wss' : 'ws';
        ws = new WebSocket(proto + '://' + location.host + '/ws/chat');

        ws.onopen = function () {
            console.log('WebSocket connected');
        };

        ws.onmessage = function (e) {
            var msg;
            try { msg = JSON.parse(e.data); } catch (err) { return; }
            handleWSMessage(msg);
        };

        ws.onclose = function () {
            console.log('WebSocket disconnected, reconnecting in 3s...');
            setTimeout(connectWS, 3000);
        };

        ws.onerror = function (err) {
            console.error('WebSocket error:', err);
        };
    }

    function sendWS(data) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(data));
        }
    }

    function handleWSMessage(msg) {
        switch (msg.type) {
            case 'stream':
                handleStream(msg);
                break;
            case 'done':
                handleDone(msg);
                break;
            case 'error':
                handleError(msg);
                break;
            case 'pong':
                break;
        }
    }

    function handleStream(msg) {
        if (!currentStreamBubble) {
            removeTyping();
            currentStreamBubble = addBubble('assistant', '');
            currentStreamContent = '';
        }
        currentStreamContent += msg.content || '';
        currentStreamBubble.querySelector('.bubble-content').innerHTML = renderMarkdown(currentStreamContent);
        scrollDown();
    }

    function handleDone(msg) {
        isStreaming = false;
        updateSendState();

        if (currentStreamBubble && currentStreamContent) {
            if (!currentConvId && msg.conversation_id) {
                currentConvId = msg.conversation_id;
                loadConversations();
            }
            if (currentConvId && msg.title) {
                updateConvTitle(currentConvId, msg.title);
            }
        }
        currentStreamBubble = null;
        currentStreamContent = '';
    }

    function handleError(msg) {
        isStreaming = false;
        updateSendState();
        removeTyping();
        if (currentStreamBubble) {
            currentStreamBubble.querySelector('.bubble-content').innerHTML =
                '<span style="color:#e53e3e;">错误: ' + escapeHtml(msg.content || '未知错误') + '</span>';
        }
        currentStreamBubble = null;
        currentStreamContent = '';
    }

    // ========== Messages & Bubbles ==========
    function addBubble(role, content) {
        var row = document.createElement('div');
        row.className = 'message-row ' + role;

        var avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        var bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = '<div class="bubble-content">' + (content ? renderMarkdown(content) : '') + '</div>';

        row.appendChild(avatar);
        row.appendChild(bubble);
        dom.messages.appendChild(row);
        scrollDown();
        return row;
    }

    function showTyping() {
        var row = document.createElement('div');
        row.className = 'message-row assistant';
        row.id = 'typingIndicator';

        var avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';

        var bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';

        row.appendChild(avatar);
        row.appendChild(bubble);
        dom.messages.appendChild(row);
        scrollDown();
    }

    function removeTyping() {
        var el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }

    function scrollDown() {
        setTimeout(function () {
            dom.messages.scrollTop = dom.messages.scrollHeight;
        }, 50);
    }

    // ========== Send Message ==========
    function sendMessage() {
        var text = dom.textarea.value.trim();
        if (!text || isStreaming) return;

        if (!currentConvId) {
            createConversation(function () {
                doSend(text);
            });
        } else {
            doSend(text);
        }
    }

    function doSend(text) {
        addBubble('user', text);
        dom.textarea.value = '';
        dom.textarea.style.height = 'auto';
        hideMentionDropdown();
        showTyping();
        isStreaming = true;
        updateSendState();

        sendWS({
            type: 'message',
            conversation_id: currentConvId,
            model_id: currentModelId,
            content: text
        });
    }

    function updateSendState() {
        dom.sendBtn.disabled = isStreaming || !dom.textarea.value.trim();
    }

    // ========== API Helpers ==========
    function getXSRFToken() {
        var input = document.querySelector('input[name=\"_xsrf\"]');
        return input ? input.value : '';
    }

    function apiFetch(url, options) {
        options = options || {};
        var headers = options.headers || {};
        headers['X-XSRFToken'] = getXSRFToken();
        if (!headers['Content-Type'] && options.body) {
            headers['Content-Type'] = 'application/json';
        }
        options.headers = headers;
        return fetch(url, options);
    }

    // ========== Conversations ==========
    function createConversation(cb) {
        apiFetch('/api/conversations', {
            method: 'POST',
            body: JSON.stringify({ title: '新对话', model_name: getModelName() })
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.code === 0) {
                    currentConvId = data.data.id;
                    loadConversations();
                    if (cb) cb();
                }
            });
    }

    function loadConversations() {
        apiFetch('/api/conversations')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.code !== 0) return;
                renderConvList(data.data);
            });
    }

    function renderConvList(convs) {
        dom.convList.innerHTML = '';
        (convs || []).forEach(function (c) {
            var item = document.createElement('div');
            item.className = 'chat-conv-item' + (c.id === currentConvId ? ' active' : '');
            item.innerHTML =
                '<span class="conv-title">' + escapeHtml(c.title || '新对话') + '</span>' +
                '<span class="conv-delete" data-id="' + c.id + '"><i class="fas fa-trash-alt"></i></span>';

            item.addEventListener('click', function (e) {
                if (e.target.closest('.conv-delete')) return;
                selectConversation(c.id);
            });

            item.querySelector('.conv-delete').addEventListener('click', function (e) {
                e.stopPropagation();
                deleteConversation(c.id);
            });

            dom.convList.appendChild(item);
        });
    }

    function selectConversation(convId) {
        currentConvId = convId;
        currentStreamBubble = null;
        currentStreamContent = '';

        document.querySelectorAll('.chat-conv-item').forEach(function (el) {
            el.classList.toggle('active', parseInt(el.querySelector('.conv-delete')?.dataset.id) === convId);
        });

        dom.messages.innerHTML = '';

        apiFetch('/api/conversations/' + convId + '?action=messages')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.code !== 0) return;
                (data.data || []).forEach(function (m) {
                    addBubble(m.role, m.content);
                });
            });
    }

    function deleteConversation(convId) {
        if (!confirm('确认删除该对话？')) return;
        apiFetch('/api/conversations/' + convId, { method: 'DELETE' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.code === 0) {
                    if (currentConvId === convId) {
                        currentConvId = null;
                        dom.messages.innerHTML = '<div class="empty-state"><i class="fas fa-comments"></i><h3>开始新的对话</h3></div>';
                    }
                    loadConversations();
                }
            });
    }

    function updateConvTitle(convId, title) {
        var items = dom.convList.querySelectorAll('.chat-conv-item');
        items.forEach(function (item) {
            var del = item.querySelector('.conv-delete');
            if (del && parseInt(del.dataset.id) === convId) {
                item.querySelector('.conv-title').textContent = title;
            }
        });
    }

    // ========== Models ==========
    function loadModels() {
        apiFetch('/api/models')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.code !== 0) return;
                models = data.data || [];
                renderModelSelect();
            });
    }

    function renderModelSelect() {
        dom.modelSelect.innerHTML = '';
        models.forEach(function (m) {
            var opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = m.name;
            if (m.is_default) {
                opt.selected = true;
                currentModelId = m.id;
            }
            dom.modelSelect.appendChild(opt);
        });
        if (!currentModelId && models.length > 0) {
            currentModelId = models[0].id;
            dom.modelSelect.value = currentModelId;
        }
        updateModelBadge();
    }

    function getModelName() {
        var sel = dom.modelSelect.selectedOptions[0];
        return sel ? sel.textContent : '';
    }

    function updateModelBadge() {
        var name = getModelName();
        dom.currentModelBadge.textContent = name || '未选择模型';
    }

    // ========== Employees ==========
    function loadEmployees() {
        apiFetch('/api/employees')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.code !== 0) return;
                employees = data.data || [];
            });
    }

    function checkMention(value, cursorPos) {
        var beforeCursor = value.substring(0, cursorPos);
        var match = beforeCursor.match(/@(\w*)$/);
        if (match) {
            var query = match[1].toLowerCase();
            var filtered = employees.filter(function (e) {
                return !query || e.name.toLowerCase().includes(query) || e.code.toLowerCase().includes(query);
            });
            if (filtered.length > 0) {
                showMentionDropdown(filtered);
                return;
            }
        }
        hideMentionDropdown();
    }

    function showMentionDropdown(items) {
        dom.mentionDropdown.innerHTML = '';
        items.forEach(function (emp) {
            var div = document.createElement('div');
            div.className = 'mention-item';
            div.innerHTML =
                '<i class="' + escapeHtml(emp.icon || 'fas fa-robot') + '"></i>' +
                '<div><div class="employee-name">@' + escapeHtml(emp.name) + '</div>' +
                '<div class="employee-desc">' + escapeHtml(emp.description || emp.code) + '</div></div>';
            div.addEventListener('click', function () {
                insertMention(emp);
            });
            dom.mentionDropdown.appendChild(div);
        });
        dom.mentionDropdown.classList.add('show');
    }

    function hideMentionDropdown() {
        dom.mentionDropdown.classList.remove('show');
    }

    function insertMention(emp) {
        var value = dom.textarea.value;
        var pos = dom.textarea.selectionStart;
        var beforeCursor = value.substring(0, pos);
        var afterCursor = value.substring(pos);
        var newBefore = beforeCursor.replace(/@\w*$/, '@' + emp.code + ' ');
        dom.textarea.value = newBefore + afterCursor;
        var newPos = newBefore.length;
        dom.textarea.selectionStart = newPos;
        dom.textarea.selectionEnd = newPos;
        dom.textarea.focus();
        hideMentionDropdown();
    }

    // ========== Quick Commands ==========
    function checkSlash(value, cursorPos) {
        var beforeCursor = value.substring(0, cursorPos);
        var match = beforeCursor.match(/(^|\s)\/(\w*)$/);
        if (match) {
            // Placeholder for future quick commands
            return true;
        }
        return false;
    }

    // ========== Helpers ==========
    function renderMarkdown(text) {
        if (!text) return '';
        var html = escapeHtml(text);
        // Code blocks
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function (_, lang, code) {
            return '<pre><code>' + code.trim() + '</code></pre>';
        });
        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Bold
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Newlines
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // ========== Event Bindings ==========
    function bindEvents() {
        dom.sendBtn.addEventListener('click', sendMessage);

        dom.textarea.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        dom.textarea.addEventListener('input', function () {
            updateSendState();
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            checkMention(this.value, this.selectionStart);
        });

        dom.textarea.addEventListener('keyup', function () {
            checkMention(this.value, this.selectionStart);
        });

        dom.textarea.addEventListener('click', function () {
            checkMention(this.value, this.selectionStart);
        });

        dom.modelSelect.addEventListener('change', function () {
            currentModelId = parseInt(this.value);
            updateModelBadge();
        });

        dom.newChatBtn.addEventListener('click', function () {
            currentConvId = null;
            dom.messages.innerHTML = '<div class="empty-state"><i class="fas fa-comments"></i><h3>开始新的对话</h3></div>';
            document.querySelectorAll('.chat-conv-item').forEach(function (el) { el.classList.remove('active'); });
            dom.textarea.focus();
        });

        dom.logoutBtn.addEventListener('click', function () {
            var form = document.createElement('form');
            form.method = 'POST';
            form.action = '/logout';
            var xsrf = document.querySelector('input[name="_xsrf"]');
            if (xsrf) {
                var input = document.createElement('input');
                input.type = 'hidden';
                input.name = '_xsrf';
                input.value = xsrf.value;
                form.appendChild(input);
            }
            document.body.appendChild(form);
            form.submit();
        });

        dom.menuToggle.addEventListener('click', function () {
            dom.sidebar.classList.toggle('open');
        });

        document.addEventListener('click', function (e) {
            if (!dom.mentionDropdown.contains(e.target) && e.target !== dom.textarea) {
                hideMentionDropdown();
            }
            if (dom.sidebar.classList.contains('open') && !dom.sidebar.contains(e.target) && e.target !== dom.menuToggle) {
                dom.sidebar.classList.remove('open');
            }
        });
    }

    // ========== Init ==========
    function init() {
        cacheDom();
        bindEvents();
        connectWS();
        loadModels();
        loadEmployees();
        loadConversations();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

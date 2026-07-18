import { useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { useEditorStore } from '../stores/editorStore';
import { api } from '../api/client';
import { Send, Sparkles } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function AIChatPanel() {
  const { currentProjectId } = useProjectStore();
  const { openFiles, activeFilePath } = useEditorStore();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hi! I\'m Diorite AI — project-aware. I use your open files, structure, symbols, MC version, mappings, deps, and recent edits for context (not whole workspace). Ask me to create a block, item, entity, etc.' }
  ]);
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim() || !currentProjectId) return;
    const userMsg: Message = { role: 'user', content: input };
    setMessages(m => [...m, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await api.aiChat({
        project_id: currentProjectId,
        message: userMsg.content,
        open_files: openFiles.map(f => f.path),
        current_file: activeFilePath,
        history: messages.map(m => ({ role: m.role, content: m.content }))
      });
      setMessages(m => [...m, { role: 'assistant', content: res.response }]);
    } catch (e:any) {
      setMessages(m => [...m, { role: 'assistant', content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-panel">
      <div className="ai-header">
        <Sparkles size={14} /> Diorite AI • Project-aware
        <span className="ai-badge">Context: open files + symbols + version</span>
      </div>
      <div className="ai-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`ai-msg ${msg.role}`}>
            <div className="ai-msg-role">{msg.role === 'user' ? 'You' : 'AI'}</div>
            <div className="ai-msg-content">{msg.content}</div>
          </div>
        ))}
        {loading && <div className="ai-msg assistant"><div className="ai-msg-content">Thinking with project context...</div></div>}
      </div>
      <div className="ai-input">
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask to create a block, fix error, explain mappings..." onKeyDown={e => e.key === 'Enter' && send()} />
        <button className="btn primary" onClick={send} disabled={loading}><Send size={14} /></button>
      </div>
      <div className="ai-footer">
        Uses: open files, structure, symbols, MC version, mappings, deps, recent edits. Efficient context.
      </div>
    </div>
  )
}

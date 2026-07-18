import { useEffect, useState } from 'react';
import { api } from '../api/client';

export function NewProjectModal({ open, onClose, onCreated }: { open: boolean, onClose: () => void, onCreated: (p: any) => void }) {
  const [templates, setTemplates] = useState<any[]>([]);
  const [name, setName] = useState('');
  const [mcVersion, setMcVersion] = useState('1.21.1');
  const [loader, setLoader] = useState('fabric');
  const [modId, setModId] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (open) {
      api.listTemplates().then(setTemplates).catch(()=>{});
    }
  }, [open]);

  if (!open) return null;

  const filteredTemplates = templates.filter(t => t.loader === loader);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      const templateId = filteredTemplates.find(t => t.mc_version === mcVersion)?.id || `${loader}-${mcVersion}`;
      const proj = await api.createProject({
        name: name.trim(),
        loader,
        mc_version: mcVersion,
        mod_id: modId.trim() || undefined,
        template_id: templateId
      });
      onCreated(proj);
      onClose();
      setName('');
      setModId('');
    } catch (e:any) {
      alert(e.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>New Minecraft Mod Project</h2>
          <p>Zero setup — templates already include Gradle, Java, mappings, run configs. Cache reuse makes second project instant.</p>
        </div>
        <div className="modal-body">
          <label>Project Name</label>
          <input value={name} onChange={e => setName(e.target.value)} placeholder="My Awesome Mod" />

          <label>Mod ID (optional, auto from name)</label>
          <input value={modId} onChange={e => setModId(e.target.value)} placeholder="awesome_mod" />

          <div className="row">
            <div className="col">
              <label>Mod Loader</label>
              <select value={loader} onChange={e => setLoader(e.target.value)}>
                <option value="fabric">Fabric</option>
                <option value="neoforge">NeoForge</option>
                <option value="forge">Forge</option>
                <option value="quilt">Quilt</option>
              </select>
            </div>
            <div className="col">
              <label>Minecraft Version</label>
              <select value={mcVersion} onChange={e => setMcVersion(e.target.value)}>
                <option>1.21.1</option>
                <option>1.21</option>
                <option>1.20.6</option>
                <option>1.20.1</option>
                <option>1.19.4</option>
              </select>
            </div>
          </div>

          <div className="templates-preview">
            <label>Templates (maintained working Gradle projects)</label>
            <div className="template-list">
              {filteredTemplates.length === 0 ? <span className="muted">No template for {loader} {mcVersion}, will use closest</span> : filteredTemplates.map(t => (
                <div key={t.id} className={`template-card ${t.mc_version === mcVersion ? 'selected' : ''}`} onClick={() => setMcVersion(t.mc_version)}>
                  <div className="t-name">{t.name}</div>
                  <div className="t-meta">{t.loader} • Java {t.java_version} • {t.id}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="cache-hint">
            <strong>Cache:</strong> Java, Gradle, Minecraft, mappings, loader files reused from ~/.diorite/cache — second Fabric 1.21.x project takes seconds.
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn secondary" onClick={onClose}>Cancel</button>
          <button className="btn primary" onClick={handleCreate} disabled={creating || !name.trim()}>
            {creating ? 'Creating...' : 'Create Project (Instant)'}
          </button>
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { api } from '../api/client';
import { Box, Package, Ghost, Monitor, FileJson, Component } from 'lucide-react';

export function ScaffoldMenu({ onCreated }: { onCreated: () => void }) {
  const { currentProjectId } = useProjectStore();
  const [type, setType] = useState<string>('block');
  const [name, setName] = useState('');

  const create = async () => {
    if (!currentProjectId || !name.trim()) return;
    const payload: any = { name: name.trim() };
    // add defaults
    if (type === 'block') { payload.material = 'STONE'; payload.creative_tab = 'BUILDING_BLOCKS'; }
    if (type === 'item') { payload.stack_size = 64; }
    if (type === 'entity') { payload.category = 'CREATURE'; payload.width = 0.6; payload.height = 1.8; }
    if (type === 'recipe') { payload.type = 'shaped'; }
    if (type === 'component') { payload.type = 'Integer'; }

    try {
      const res = await api.scaffold(currentProjectId, type, payload);
      console.log('scaffolded', res);
      alert(`Created ${type}: ${JSON.stringify(res.files_created)}`);
      onCreated();
      setName('');
    } catch (e:any) {
      alert(e.message);
    }
  };

  if (!currentProjectId) return null;

  const types = [
    { id: 'block', label: 'Block', icon: Box },
    { id: 'item', label: 'Item', icon: Package },
    { id: 'entity', label: 'Entity', icon: Ghost },
    { id: 'screen', label: 'Screen', icon: Monitor },
    { id: 'recipe', label: 'Recipe', icon: FileJson },
    { id: 'component', label: 'Data Component', icon: Component },
  ];

  return (
    <div className="scaffold-menu">
      <div className="scaffold-title">New Minecraft... </div>
      <div className="scaffold-types">
        {types.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} className={`scaffold-type ${type === t.id ? 'active' : ''}`} onClick={() => setType(t.id)}>
              <Icon size={14} /> {t.label}
            </button>
          );
        })}
      </div>
      <div className="scaffold-form">
        <input placeholder={`${type} name e.g., ruby_block`} value={name} onChange={e => setName(e.target.value)} />
        <button className="btn primary" onClick={create} disabled={!name.trim()}>Create</button>
      </div>
      <div className="scaffold-hint">
        Generates files + registration automatically. Built on normal source files.
      </div>
    </div>
  )
}

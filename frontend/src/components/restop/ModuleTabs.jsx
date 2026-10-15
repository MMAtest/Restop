import React from 'react';
import './module-tabs.css';

/** Shared segmented navigation for a module's subviews.
 * Unlike decorative tabs, every option invokes the actual feature callback.
 * aria-pressed is used because the subview controls may be outside this component.
 */
export default function ModuleTabs({label,items,value,onChange,className=''}) {
  return <div className={`rt-module-tabs ${className}`} role="group" aria-label={label}>
    {items.filter(item=>!item.hidden).map(item=><button
      key={item.id} type="button" disabled={item.disabled} onClick={()=>onChange(item.id)} aria-pressed={item.id===value}
      className={`rt-module-tab ${item.id===value?'is-active':''}`}>
      <span className="rt-module-tab-label">{item.label}</span>{Number.isFinite(item.count)&&<span className="rt-module-tab-count">{item.count}</span>}
    </button>)}
  </div>;
}

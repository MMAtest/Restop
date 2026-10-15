import React from 'react';
import {CheckCircle,WarningCircle,Info,X} from '@phosphor-icons/react';

/** Persistent inline action feedback: never pretend a request succeeded. */
export default function ActionNotice({notice,onDismiss}) {
  if(!notice?.message)return null;
  const Icon=notice.kind==='error'?WarningCircle:notice.kind==='success'?CheckCircle:Info;
  return <div className={`rt-action-notice rt-action-notice-${notice.kind||'info'}`} role={notice.kind==='error'?'alert':'status'}>
    <Icon size={19} weight="regular"/><span>{notice.message}</span><button type="button" aria-label="Fermer le message" onClick={onDismiss}><X size={17}/></button>
  </div>;
}

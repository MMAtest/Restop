import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import DeliveryRulesConfig from './DeliveryRulesConfig';
test('same-day delivery and a midnight cutoff remain visible as zero',async()=>{
 global.IS_REACT_ACT_ENVIRONMENT=true;
 const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host);
 await act(async()=>root.render(<DeliveryRulesConfig supplier={{nom:'Test',delivery_rules:{order_days:[],delivery_days:[],order_deadline_hour:0,delivery_delay_days:0,delivery_time:'00:00'}}} onSave={()=>{}} onCancel={()=>{}}/>));
 const inputs=host.querySelectorAll('input[type=number]');
 expect(inputs[0].value).toBe('0');expect(inputs[1].value).toBe('0');
 await act(async()=>root.unmount());host.remove();
});

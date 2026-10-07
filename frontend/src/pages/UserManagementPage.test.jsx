import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import UserManagementPage from './UserManagementPage';
import {apiFetch} from '../utils/api';
jest.mock('../utils/api',()=>({apiFetch:jest.fn()}));
test('a team loading error is visible and offers a retry',async()=>{
 global.IS_REACT_ACT_ENVIRONMENT=true;const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host);
 apiFetch.mockResolvedValue({ok:false,status:503});
 await act(async()=>root.render(<UserManagementPage currentUser={{role:'patron'}}/>));
 expect(host.querySelector('[role=alert]')?.textContent).toContain('utilisateurs');
 await act(async()=>root.unmount());host.remove();jest.resetAllMocks();
});

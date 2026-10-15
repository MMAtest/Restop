jest.mock('axios',()=>({defaults:{headers:{common:{}}}}));
import {apiFetch} from './api';

afterEach(()=>{localStorage.clear();jest.restoreAllMocks()});
test('envoie Authorization au backend même avec API relative',async()=>{
 localStorage.setItem('user_session',JSON.stringify({session_id:'test-session',user:{id:'mock',role:'patron'}}));
 const captured=[];
 global.fetch=jest.fn(async (_url,init)=>{captured.push(init.headers);return {ok:true,json:async()=>({})}});
 await apiFetch('/api/stocks');
 expect(captured[0].get('Authorization')).toBe('Bearer test-session');
});

test('n’envoie jamais le jeton à une URL externe arbitraire',async()=>{
 localStorage.setItem('user_session',JSON.stringify({session_id:'test-session',user:{id:'mock',role:'patron'}}));
 const captured=[];
 global.fetch=jest.fn(async (_url,init)=>{captured.push(init.headers);return {ok:true,json:async()=>({})}});
 await apiFetch('https://example.org/other');
 expect(captured[0].has('Authorization')).toBe(false);
});

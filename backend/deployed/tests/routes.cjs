const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const babel=require('../../../frontend/node_modules/@babel/core');
const ts=require('../../../frontend/node_modules/@babel/plugin-transform-typescript');
const common=require('../../../frontend/node_modules/@babel/plugin-transform-modules-commonjs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../index.ts'),'utf8');
const code=babel.transformSync(source,{filename:'index.ts',configFile:false,babelrc:false,plugins:[ts,common]}).code;
let handler,role='employe_cuisine',rpcCalls=0;
const chain=new Proxy({}, {get:(_,key)=>key==='then'? (resolve)=>resolve({data:{user_id:'u',restaurant_id:'r',role,is_active:true},error:null}):()=>chain});
const client={auth:{getUser:async()=>({data:{user:{id:'u'}}})},from:()=>chain,rpc:async()=>{rpcCalls++;return {error:{message:'Transactional validation failed'}};}};
vm.runInNewContext(code,{exports:{},require:name=>name.includes('supabase')?{createClient:()=>client}:{},Deno:{env:{get:()=>''},serve:fn=>handler=fn},Response,Request,URL,console,crypto});
const call=(path,method='GET',data,token='restop-demo-public-v1')=>handler(new Request('https://example.test/api'+path,{method,headers:{...(token?{authorization:'Bearer '+token}:{}),'content-type':'application/json'},...(data?{body:JSON.stringify(data)}:{})}));
(async()=>{
 assert.equal((await call('/produits','GET',null,null)).status,401);
 assert.equal((await call('/admin/users','GET',null,'user-token')).status,403);
 assert.equal((await call('/orders','POST',{items:[]},'user-token')).status,403);
 assert.equal((await call('/unknown')).status,404);
 assert.ok((await (await call('/unites')).json()).unites.some(u=>u.code==='kg'));
 assert.ok(Array.isArray((await (await call('/formes-decoupe')).json()).predefined));
 assert.equal((await call('/orders','POST',{items:[{quantity:-1,unit_price:2}]})).status,400);
 assert.equal((await call('/recettes','POST',{nom:'x',portions:0})).status,400);
 assert.equal((await call('/recettes','PUT',{nom:'x',portions:1})).status,501); // only resource IDs may be edited
 assert.equal((await call('/recettes/10000000-0000-4000-8000-000000000003','PUT',{nom:'x',portions:1,ingredients:[]})).status,400);
 assert.equal(rpcCalls,1); // PUT reaches the same atomic service path as POST
 console.log('10 backend route/security checks passed');
})().catch(e=>{console.error(e);process.exitCode=1;});

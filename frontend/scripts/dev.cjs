const {spawn}=require('node:child_process');
const args=process.argv.slice(2);
const value=(k,d)=>args.includes(k)?args[args.indexOf(k)+1]:d;
const child=spawn(process.execPath,[require.resolve('@craco/craco/dist/bin/craco.js'),'start'],{stdio:'inherit',env:{...process.env,HOST:value('--host','0.0.0.0'),PORT:value('--port','4173'),BROWSER:'none',WDS_SOCKET_PORT:'0'}});
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>child.kill(signal));
child.on('exit',code=>process.exit(code||0));

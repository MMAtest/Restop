import React, {useState,useEffect} from 'react';
import {CalendarBlank,CaretLeft,CaretRight} from '@phosphor-icons/react';
export default function DateRangePicker({onDateRangeChange}) {
  const [period,setPeriod]=useState('today');
  const [offset,setOffset]=useState(0);
  const [start,setStart]=useState('');
  const [end,setEnd]=useState('');
  const today=new Date(); today.setHours(12,0,0,0);
  const a=new Date(today), b=new Date(today);
  const weekday=(today.getDay()+6)%7;
  if(period==='today'||period==='yesterday'){a.setDate(a.getDate()+(period==='yesterday'?-1:0)+offset);b.setTime(a.getTime());}
  if(period==='thisWeek')a.setDate(a.getDate()-weekday);
  if(period==='lastWeek'){a.setDate(a.getDate()-weekday-7);b.setDate(b.getDate()-weekday-1);}
  if(period==='thisMonth')a.setDate(1);
  if(period==='lastMonth'){a.setMonth(a.getMonth()-1,1);b.setDate(0);}
  if(period==='custom'){a.setTime(new Date(start+'T12:00:00').getTime());b.setTime(new Date(end+'T12:00:00').getTime());}
  const valid=Number.isFinite(a.getTime())&&Number.isFinite(b.getTime())&&a<=b;
  const label=valid?(a.getTime()===b.getTime()?a.toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'}):`Du ${a.toLocaleDateString('fr-FR')} au ${b.toLocaleDateString('fr-FR')}`):'Choisissez une période';
  useEffect(()=>{if(valid)onDateRangeChange({startDate:a,endDate:b,label});},[period,offset,start,end]); // Parent callback updates analytics only.
  return <div className="rt-date-picker"><label htmlFor="analysis-period"><CalendarBlank size={20}/>Période</label><select id="analysis-period" value={period} onChange={e=>{setPeriod(e.target.value);setOffset(0);}}>{[['today',"Aujourd’hui"],['yesterday','Hier'],['thisWeek','Cette semaine'],['lastWeek','Semaine dernière'],['thisMonth','Ce mois'],['lastMonth','Mois dernier'],['custom','Dates personnalisées']].map(([v,l])=><option key={v} value={v}>{l}</option>)}</select><div className="rt-date-summary"><button aria-label="Jour précédent" disabled={!['today','yesterday'].includes(period)} onClick={()=>setOffset(offset-1)}><CaretLeft/></button><span>{label}</span><button aria-label="Jour suivant" disabled={!['today','yesterday'].includes(period)} onClick={()=>setOffset(offset+1)}><CaretRight/></button></div>{period==='custom'&&<div className="rt-date-custom"><label>Du <input type="date" value={start} onChange={e=>setStart(e.target.value)}/></label><label>Au <input type="date" value={end} min={start} onChange={e=>setEnd(e.target.value)}/></label>{start&&end&&!valid&&<p className="rt-date-error" role="alert">La date de fin doit être postérieure ou égale à la date de début.</p>}</div>}</div>;
}

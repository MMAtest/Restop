import {cutForms,cutFormCode,asList,number,categories,units,recipe,missionGroups} from './contracts';
import {readSession} from './session';
import {csvCell} from './export';
test('malformed lists and null numbers are safe without losing numeric strings',()=>{
 expect(asList({categories:null},'categories')).toEqual([]);expect(number('12.30')).toBe(12.3);expect(number(null)).toBe(0);expect(number('NaN')).toBe(0);
 expect(categories(['Plat'])).toEqual(['Plat']);expect(units([]).length).toBeGreaterThan(0);
 expect(recipe({prix_vente:'24.30',ingredients:null}).prix_vente).toBe(24.3);
});
test('missions returned as a list remain visible for the assigned user',()=>{expect(missionGroups([{id:'m',assigned_to_user_id:'u'}],'u').assigned_to_me).toHaveLength(1);});
test('a corrupt saved session cannot crash startup',()=>{localStorage.setItem('user_session','{invalid');expect(readSession()).toBeNull();expect(localStorage.getItem('user_session')).toBeNull();});
test('CSV user fields cannot execute spreadsheet formulas',()=>{expect(csvCell('=SUM(A1)')).toBe('"\'=SUM(A1)"');expect(csvCell('a"b')).toBe('"a""b"');});

test('cut form labels and codes accept both server strings and legacy objects',()=>{
 const forms=cutForms({predefined:['Haché',{id:'julienne',nom:'Julienne'}]});
 expect(forms.predefined.find(f=>f.id===cutFormCode('haché')).nom).toBe('Haché');
 expect(forms.predefined.some(f=>f.id==='sauce')).toBe(true);
 expect(forms.predefined.every(f=>f.id && f.nom)).toBe(true);
});

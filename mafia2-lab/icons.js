// MAFIA 2 pixel icons. Each is drawn on a 10 by 10 grid, so at button size (20px) one icon pixel is 2px,
// the same as the game's own pixels. Never show one below scale 2. The review sheet (icons.html) carries
// its own copy of these grids because it has to be a single file; change both together.
(function(){
const PAL={K:'#1a1430',W:'#ffffff',P:'#f6dfae',p:'#e9c88a',R:'#e4544f',r:'#a92b2c',G:'#ffd25e',g:'#d39b2a',Y:'#fff2a8',
  B:'#4a7bd0',b:'#2b4a8a',L:'#9fd0ff',E:'#5fc46f',e:'#2f7a3f',S:'#b8c2d4',s:'#6f7b92',H:'#5a5290',h:'#3b3468',
  O:'#c58a4a',o:'#7a4a2a',V:'#9a48ad',v:'#5e2a86',M:'#f07ab0',m:'#b8457e'};
// Drawn on a 10 by 10 grid. At button size one icon pixel is 2px, the same as the game's own pixels.
const GRID=10,E='..........';
const ICONS={
mafia:[E,E,'...KKKK...','..KHHHHK..','..KHHHhK..','..KRRRrK..','.KKhhhhKK.','KHHHHHHHhK','.KKKKKKKK.',E],
doctor:[E,'...KKKK...','...KEEK...','.KKKEEKKK.','.KEEEEEeK.','.KEEEEEeK.','.KKKEeKKK.','...KEeK...','...KKKK...',E],
civilian:['....KK....','...KRRK...','..KRRRRK..','.KRRRRRrK.','KKKKKKKKKK','.KPPPPPPK.','.KPooPGPK.','.KPooPPPK.','.KKKKKKKK.',E],
detective:['..KKKK....','.KLLLLK...','KLWLLLLK..','KLLLLLLK..','KLLLLLLK..','KLLLLLLK..','.KLLLLKK..','..KKKKOOK.','.......KOK','........KK'],
jester:['..KK..KK..','.KVVKKEEK.','KVVVVEEEEK','KVVVVEEEEK','KVKvvEeKEK','KVKKKKKKEK','KVK....KEK','.K......K.','KGK....KGK','.K......K.'],
bodyguard:[E,'.KKKKKKKK.','.KGGGgggK.','.KGWGgggK.','.KGGGgggK.','.KGGGgggK.','..KGGggK..','...KGgK...','....KK....',E],
framer:[E,'.KKKKKKKK.','KMMMMMMMMK','KMKKMMKKMK','KMKKMMKKMK','KMMMMMMMMK','KMKMMMMKMK','.KMKKKKMK.','..KmmmmK..','...KKKK...'],
eye:[E,E,'..KKKKKK..','.KWWWWWWK.','KWWBKKBWWK','KWWBKKBWWK','.KWWWWWWK.','..KKKKKK..',E,E],
rain:[E,'...KKK....','.KKWWWKK..','KWWWWWWWK.','KSSSSSSSK.','.KKKKKKK..',E,'.B..B..B..','B..B..B...',E],
moon:['...KKKK...','..KGGGK...','.KGGGK....','.KGGK...g.','.KGGK..ggg','.KGGK...g.','.KGGGK....','..KGGGK...','...KKKK...',E],
sun:['....gg....','.g......g.','...KKKK...','..KGGGGK..','g.KGYGGK.g','g.KGGGGK.g','..KGGGgK..','...KKKK...','.g......g.','....gg....'],
notes:[E,'.KKKKKKKK.','.KWWWWWWK.','.KWsssWWK.','.KWWWWWWK.','.KWssssWK.','.KWWWWWWK.','.KWsssWWK.','.KKKKKKKK.',E],
lock:['...KKKK...','..KSSSSK..','..KSKKSK..','.KKKKKKKK.','.KGGGGGGK.','.KGGKKGGK.','.KGGKKGGK.','.KggggggK.','.KKKKKKKK.',E],
binoculars:[E,'.KKK..KKK.','KSSSKKSSSK','KSSSKKSSSK','KSSSSSSSSK','KKKKKKKKKK','KLLLKKLLLK','KLWLKKLWLK','.KKK..KKK.',E],
mute:[E,'....KK....','...KSK.R.R','.KKSSK..R.','.KSSSK.R.R','.KSSSK....','.KKSSK....','...KSK....','....KK....',E],
hanger:['....KK....','...K..K...','......K...','....KKK...','...KOOOK..','..KOKKKOK.','.KOK...KOK','KOOKKKKKOK','KKKKKKKKKK',E],
skull:['..KKKKKK..','.KWWWWWWK.','KWWWWWWWWK','KWKKWWKKWK','KWKKWWKKWK','KWWWKKWWWK','.KWWWWWWK.','..KWKKWK..','..KKKKKK..',E],
ghost:['..KKKKKK..','.KWWWWWWK.','KWWWWWWWWK','KWKKWWKKWK','KWKKWWKKWK','KWWWWWWWWK','KWWWKKWWWK','KWWWWWWWWK','KWKKWKKWWK','KK..K..KK.'],
bat:[E,'K........K','KK.K..K.KK','KHKKHHKKHK','KHHHHHHHHK','KHHRHHRHHK','.KHHHHHHK.','..KHKKHK..','...K..K...',E],
spider:['K...KK...K','.K.KHHK.K.','..KHHHHK..','KKKHRRHKKK','..KHHHHK..','.KKHHHHKK.','K..KHHK..K','...KKKK...','..K....K..',E],
boo:['..KKK.KKK.','..KRK.KRK.','..KRK.KRK.','..KRK.KRK.','..KRK.KRK.','..KKK.KKK.',E,'..KKK.KKK.','..KRK.KRK.','..KKK.KKK.'],
heart:[E,'.KKK..KKK.','KRRRKKRRRK','KRWRRRRRRK','KRRRRRRRrK','.KRRRRRrK.','..KRRRrK..','...KRrK...','....KK....',E],
coin:[E,'..KKKKKK..','.KGGGGGGK.','KGYGGGGGgK','KGYGggGGgK','KGGGggGGgK','KGGGGGGggK','.KGGggggK.','..KKKKKK..',E],
chat:[E,'.KKKKKKKK.','KWWWWWWWWK','KWKWKWKWWK','KWWWWWWWWK','.KKKWWKKK.','...KWK....','...KK.....',E,E],
vote:['...KKKK...','...KWWK...','...KRWK...','KKKKWWKKKK','KOOKKKKOOK','KOOOOOOOOK','KOOOOOOOOK','KooooooooK','KKKKKKKKKK',E],
knife:['....KK....','...KSWK...','...KSWK...','...KSWK...','...KSWK...','.KKKSWKKK.','.KggggggK.','.KKKooKKK.','...KooK...','...KKKK...'],
door:['.KKKKKKKK.','.KOOOOOOK.','.KOKKKKOK.','.KOKooKOK.','.KOKKKKOK.','.KOOOOGOK.','.KOKKKKOK.','.KOKooKOK.','.KOKKKKOK.','.KKKKKKKK.'],
right:[E,'..KK......','..KgKK....','..KgggKK..','..KgggggK.','..KgggggK.','..KgggKK..','..KgKK....','..KK......',E],
check:[E,'........KK','.......KEK','......KEEK','.KK..KEEK.','KEEKKEEK..','KEEEEEK...','.KEEEK....','..KKK.....',E],
cross:[E,'.KK....KK.','KRRK..KRRK','.KRRKKRRK.','..KRRRRK..','..KRRRRK..','.KRRKKRRK.','KRRK..KRRK','.KK....KK.',E],
skip:[E,E,'KK...KK...','KgKK.KgKK.','KgggKKgggK','KgggKKgggK','KgKK.KgKK.','KK...KK...',E,E],
sleep:['....BBBBBB','........BB','.......BB.','......BB..','.....BB...','....BBBBBB','BBBB......','..BB......','.BB.......','BBBB......'],
hourglass:['KKKKKKKKKK','.KWWWWWWK.','.KWGGGGWK.','..KWGGWK..','...KWWK...','...KWGK...','..KWWGWK..','.KWGGGGWK.','.KWGGGGWK.','KKKKKKKKKK'],
case:[E,'...KKKK...','...K..K...','KKKKKKKKKK','KOOOOOOOOK','KKKKGGKKKK','KoooGGoooK','KooooooooK','KKKKKKKKKK',E],
rec:[E,E,'...KKKK...','..KRRRRK..','..KRWRRK..','..KRRRRK..','..KRRRrK..','...KKKK...',E,E],
};
// the other three arrows are the right arrow, turned
ICONS.left=ICONS.right.map(r=>[...r].reverse().join(''));
ICONS.down=ICONS.right.map((_,y)=>ICONS.right.map(r=>r[y]).join(''));
ICONS.up=[...ICONS.down].reverse();
const URLS={};
function url(name){
  if(URLS[name])return URLS[name];
  const g=ICONS[name],c=document.createElement('canvas');c.width=c.height=GRID;const x=c.getContext('2d');
  g.forEach((row,y)=>[...row].forEach((ch,i)=>{if(ch==='.')return;x.fillStyle=PAL[ch]||'#f0f';x.fillRect(i,y,1,1);}));
  return URLS[name]=c.toDataURL();
}
// ic('lock') -> an <img> at button size; ic('skull',3) for headings; pass 'solo' or 'after' as the third argument
// for an icon on its own, or one that comes after its label
window.ic=function(name,scale,cls){const s=Math.max(2,scale||2);if(!ICONS[name])return'';
  return `<img class="ic${cls?' '+cls:''}" src="${url(name)}" width="${GRID*s}" height="${GRID*s}" alt="">`;};
window.M2_ICONS=ICONS;
})();

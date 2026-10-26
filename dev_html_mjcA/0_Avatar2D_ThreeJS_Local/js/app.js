/*
 * Avatar Studio — HTML5 Canvas 2D + Three.js OrthographicCamera
 *
 * ① drawAvatar(): 얼굴/몸/의상을 HTML5 Canvas의 벡터 도형으로 그립니다.
 * ② 캔버스를 CanvasTexture에 연결하고 Three.js 정사영 카메라로 표시합니다.
 * ③ Three.js가 없거나 파일 경로가 잘못되어도 Canvas 2D가 남도록 설계했습니다.
 * 모든 메뉴·저장·PNG 내보내기는 오프라인 Canvas 상태에서도 작동합니다.
 */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const fields = ['avatarName','bodyType','pose','face','skin','eyes','iris','brows','mouth','freckles','hairStyle','hairColor','top','topColor','bottom','bottomColor','shoes','shoeColor','glasses','hat','earrings','necklace','bag','accColor'];
const selectValues = {
 bodyType:['standard','petite','tall','broad'],pose:['normal','wave','handsup'],
 face:['round','oval','square','heart','long'],eyes:['normal','round','smile','sharp','wink'],
 brows:['soft','straight','arched'],mouth:['smile','happy','neutral','surprise'],
 hairStyle:['short','bob','long','curly','ponytail','bun','spiky'],
 top:['tshirt','hoodie','shirt','jacket','sweater'],bottom:['pants','jeans','shorts','skirt'],
 shoes:['sneakers','boots','loafers'],glasses:['none','round','square','sunglasses'],
 hat:['none','cap','beanie','headband','beret'],earrings:['none','stud','hoop'],
 necklace:['none','chain','pendant'],bag:['none','crossbody','backpack']
};
const COLORS=['skin','iris','hairColor','topColor','bottomColor','shoeColor','accColor'];
const base = {
 avatarName:'나의 아바타',bodyType:'standard',pose:'normal',face:'round',skin:'#EAB48E',
 eyes:'normal',iris:'#41322B',brows:'soft',mouth:'smile',freckles:false,
 hairStyle:'short',hairColor:'#33243C',top:'tshirt',topColor:'#617EE7',
 bottom:'pants',bottomColor:'#33435D',shoes:'sneakers',shoeColor:'#F6F8FF',
 glasses:'none',hat:'none',earrings:'none',necklace:'none',bag:'none',accColor:'#E9B949'
};
const templates = [
 {id:'sky',name:'하늘',set:{...base,avatarName:'하늘',hairStyle:'bob',topColor:'#617EE7',bottomColor:'#33435D',mouth:'smile'}},
 {id:'mint',name:'초록',set:{...base,avatarName:'초록',bodyType:'petite',face:'heart',skin:'#F0BD9D',hairStyle:'long',hairColor:'#62473D',top:'sweater',topColor:'#56AC90',bottom:'skirt',bottomColor:'#49607A',earrings:'stud'}},
 {id:'noir',name:'누아',set:{...base,avatarName:'누아',bodyType:'tall',face:'oval',skin:'#B9805D',eyes:'sharp',hairStyle:'short',hairColor:'#181C2B',top:'jacket',topColor:'#384D65',bottom:'jeans',glasses:'square'}},
 {id:'pop',name:'팝',set:{...base,avatarName:'팝',face:'round',skin:'#E1A77D',hairStyle:'curly',hairColor:'#A05630',top:'hoodie',topColor:'#F27882',bottom:'shorts',bottomColor:'#3B5375',shoes:'sneakers',shoeColor:'#FFE6A2',mouth:'happy'}},
 {id:'sport',name:'스포츠',set:{...base,avatarName:'스포츠',bodyType:'broad',skin:'#D9966E',pose:'wave',hairStyle:'spiky',hairColor:'#30211C',top:'tshirt',topColor:'#F6A23C',bottom:'shorts',bottomColor:'#35485A',hat:'cap',accColor:'#F9C648'}},
 {id:'dream',name:'드림',set:{...base,avatarName:'드림',bodyType:'petite',face:'oval',skin:'#F0C8B1',hairStyle:'bun',hairColor:'#5C387A',top:'shirt',topColor:'#E6E9FA',bottom:'skirt',bottomColor:'#8C77C5',hat:'headband',glasses:'round',necklace:'pendant',accColor:'#BE92FF'}}
];
const captions={
 bodyType:{standard:'기본',petite:'아담함',tall:'키 큰',broad:'넓은 어깨'},
 face:{round:'둥근 얼굴',oval:'계란형',square:'각진 얼굴',heart:'하트형',long:'긴 얼굴'},
 hairStyle:{short:'숏컷',bob:'단발',long:'긴 머리',curly:'곱슬',ponytail:'포니테일',bun:'올림머리',spiky:'스파이크'},
 top:{tshirt:'티셔츠',hoodie:'후드티',shirt:'셔츠',jacket:'재킷',sweater:'스웨터'},
 bottom:{pants:'바지',jeans:'청바지',shorts:'반바지',skirt:'스커트'}
};
let state={...base}, chosen='sky', zoom=1, three=null, toastTimer=null;
const avatarCanvas=$('avatarCanvas');const avatarCtx=avatarCanvas.getContext('2d');

// ---------- Canvas 2D 벡터 헬퍼 ----------
const INK='#403748';
function paint(ctx, path, fill, stroke=INK, width=5){
 ctx.beginPath();path(ctx);if(fill){ctx.fillStyle=fill;ctx.fill();}
 if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke();}
}
function ell(ctx,x,y,rx,ry,fill,stroke=INK,lw=4){paint(ctx,c=>c.ellipse(x,y,rx,ry,0,0,Math.PI*2),fill,stroke,lw);}
function line(ctx,points,color=INK,w=5){ctx.beginPath();ctx.moveTo(points[0][0],points[0][1]);for(let i=1;i<points.length;i++)ctx.lineTo(points[i][0],points[i][1]);ctx.strokeStyle=color;ctx.lineWidth=w;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke();}
function lighten(hex,delta){const n=parseInt(hex.slice(1),16);return '#'+[n>>16,(n>>8)&255,n&255].map(v=>Math.max(0,Math.min(255,v+delta)).toString(16).padStart(2,'0')).join('');}
function rect(ctx,x,y,w,h,r,color,stroke=INK,lw=4){ctx.beginPath();ctx.roundRect(x,y,w,h,r);if(color){ctx.fillStyle=color;ctx.fill();}if(stroke){ctx.lineWidth=lw;ctx.strokeStyle=stroke;ctx.stroke();}}
function headDimensions(face){return {round:[1,1],oval:[.94,1.06],square:[1.07,.98],heart:[1.02,1],long:[.91,1.13]}[face]||[1,1];}

// ---------- 하체 / 신발 ----------
function legs(ctx,c){
 const skin=c.skin, pant=c.bottomColor;
 const trousers=c.bottom==='pants'||c.bottom==='jeans';
 // 항상 기본 다리를 그린 다음, 바지/반바지/스커트를 앞에 얹는다.
 paint(ctx,p=>{p.moveTo(331,660);p.lineTo(448,660);p.lineTo(422,986);p.lineTo(344,986);p.closePath();},skin);
 paint(ctx,p=>{p.moveTo(452,660);p.lineTo(567,660);p.lineTo(552,986);p.lineTo(476,986);p.closePath();},skin);
 if(trousers){
  paint(ctx,p=>{p.moveTo(327,658);p.lineTo(450,658);p.lineTo(424,966);p.lineTo(334,966);p.closePath();},pant);
  paint(ctx,p=>{p.moveTo(450,658);p.lineTo(572,658);p.lineTo(560,966);p.lineTo(474,966);p.closePath();},pant);
  line(ctx,[[450,675],[444,754]],lighten(pant,-28),4);
  if(c.bottom==='jeans'){
   line(ctx,[[347,729],[414,732]],lighten(pant,32),3);
   line(ctx,[[488,730],[554,731]],lighten(pant,32),3);
   line(ctx,[[345,937],[415,938]],lighten(pant,50),4);
   line(ctx,[[484,937],[547,938]],lighten(pant,50),4);
  }
 }else if(c.bottom==='shorts'){
  paint(ctx,p=>{p.moveTo(327,660);p.lineTo(453,660);p.lineTo(443,779);p.lineTo(334,779);p.closePath();},pant);
  paint(ctx,p=>{p.moveTo(453,660);p.lineTo(572,660);p.lineTo(563,779);p.lineTo(461,779);p.closePath();},pant);
  line(ctx,[[341,763],[438,763]],lighten(pant,35),4);line(ctx,[[471,763],[556,763]],lighten(pant,35),4);
 }else if(c.bottom==='skirt'){
  paint(ctx,p=>{p.moveTo(343,655);p.lineTo(553,655);p.bezierCurveTo(576,705,610,787,614,803);p.quadraticCurveTo(452,836,288,803);p.bezierCurveTo(303,740,323,688,343,655);p.closePath();},pant);
  for(const x of [369,437,513,562])line(ctx,[[x,716],[450+(x-450)*1.32,802]],lighten(pant,-20),3);
 }
 // 신발은 항상 맨 앞에 그린다.
 const shoe=c.shoeColor;
 const boots=c.shoes==='boots',loafers=c.shoes==='loafers';
 if(boots){rect(ctx,324,909,112,91,19,shoe);rect(ctx,467,909,112,91,19,shoe)}
 paint(ctx,p=>{p.moveTo(342,962);p.lineTo(423,962);p.lineTo(451,996);p.quadraticCurveTo(452,1013,432,1018);p.lineTo(317,1018);p.quadraticCurveTo(294,1007,315,987);p.closePath();},shoe);
 paint(ctx,p=>{p.moveTo(473,962);p.lineTo(552,962);p.lineTo(591,993);p.quadraticCurveTo(605,1016,580,1018);p.lineTo(459,1018);p.quadraticCurveTo(443,1008,456,991);p.closePath();},shoe);
 if(!loafers){
  line(ctx,[[318,1004],[446,1004]],lighten(shoe,-24),5);line(ctx,[[461,1004],[586,1004]],lighten(shoe,-24),5);
  if(!boots){for(const xx of [364,505])for(let y=978;y<1000;y+=9)line(ctx,[[xx-22,y],[xx+14,y]],'#8A95AB',2.6);}
 }else{line(ctx,[[322,995],[432,995]],'#80796E',4);line(ctx,[[462,995],[582,995]],'#80796E',4);}
}
function arm(ctx,c,side){
 const sign=side==='left'?-1:1;const pos=c.pose;
 ctx.save();ctx.translate(450+sign*145,453);ctx.scale(sign,1);
 if(pos==='wave'&&side==='right')ctx.rotate(-2.2);
 if(pos==='handsup')ctx.rotate(-2.1);
 paint(ctx,p=>{p.moveTo(-7,-6);p.quadraticCurveTo(38,-24,64,43);p.lineTo(82,248);p.quadraticCurveTo(86,280,56,290);p.quadraticCurveTo(27,290,26,251);p.lineTo(5,115);p.lineTo(-19,37);p.closePath();},c.skin);
 // 손 (약간 각도가 다른 포즈도 그룹과 함께 회전)
 ell(ctx,71,281,31,36,c.skin);
 // 소매
 const sleeveLength=(c.top==='jacket'||c.top==='hoodie'||c.top==='sweater')?190:95;
 paint(ctx,p=>{p.moveTo(-7,-5);p.quadraticCurveTo(29,-18,62,31);p.lineTo(66+(sleeveLength>100?9:2),sleeveLength);p.lineTo(15+(sleeveLength>100?10:0),sleeveLength+6);p.lineTo(5,114);p.lineTo(-19,32);p.closePath();},c.topColor);
 line(ctx,[[21,sleeveLength-7],[67,sleeveLength-7]],lighten(c.topColor,-22),4);
 ctx.restore();
}
function hairBack(ctx,c){
 if(!['long','bob','ponytail','curly'].includes(c.hairStyle))return;
 let b=c.hairColor;
 if(c.hairStyle==='long'){
  paint(ctx,p=>{p.moveTo(332,191);p.bezierCurveTo(296,244,297,434,287,554);p.quadraticCurveTo(329,573,381,545);p.lineTo(413,233);p.closePath();},b);
  paint(ctx,p=>{p.moveTo(570,183);p.bezierCurveTo(609,290,609,449,619,553);p.quadraticCurveTo(566,579,529,545);p.lineTo(496,227);p.closePath();},b);
 }else if(c.hairStyle==='bob'){
  paint(ctx,p=>{p.moveTo(335,181);p.bezierCurveTo(293,248,304,433,323,465);p.lineTo(388,463);p.lineTo(415,203);p.closePath();},b);
  paint(ctx,p=>{p.moveTo(565,181);p.bezierCurveTo(607,248,596,433,577,465);p.lineTo(514,463);p.lineTo(489,203);p.closePath();},b);
 }else if(c.hairStyle==='ponytail'){
  paint(ctx,p=>{p.moveTo(570,188);p.bezierCurveTo(650,209,651,373,610,492);p.quadraticCurveTo(560,470,555,430);p.closePath();},b);
 }else if(c.hairStyle==='curly'){
  for(let i=0;i<8;i++){
    const side=i<4?-1:1;const yy=176+(i%4)*65;
    ell(ctx,450+side*(136+(i%3)*14),yy,49,55,b);
  }
 }
}
function drawFace(ctx,c){
 const skin=c.skin,shadow=lighten(skin,-19),shape=c.face;
 ctx.save();const [sx,sy]=headDimensions(shape);ctx.translate(450,302);ctx.scale(sx,sy);ctx.translate(-450,-302);
 hairBack(ctx,c);
 ell(ctx,306,315,32,45,skin);ell(ctx,594,315,32,45,skin);
 paint(ctx,p=>{
  p.moveTo(450,165);
  p.bezierCurveTo(356,159,319,215,318,276);
  if(shape==='square'){p.lineTo(319,353);p.quadraticCurveTo(332,421,406,426);p.lineTo(492,426);p.quadraticCurveTo(577,420,581,351);p.lineTo(583,276);}
  else if(shape==='heart'){p.bezierCurveTo(304,343,365,402,450,427);p.bezierCurveTo(537,399,593,345,583,276);}
  else {p.bezierCurveTo(307,355,349,422,450,432);p.bezierCurveTo(551,422,593,355,582,276);}
  p.bezierCurveTo(575,209,534,159,450,165);p.closePath();
 },skin);
 // 피부 톤 음영 / 볼
 ell(ctx,359,339,27,13,lighten(skin,8),null);
 ell(ctx,541,339,27,13,lighten(skin,8),null);
 if(c.freckles){ctx.fillStyle='#A56857';for(const xx of [346,359,372,527,540,553])for(const yy of [326,335]){ctx.beginPath();ctx.arc(xx+(yy%3)*2,yy,3,0,Math.PI*2);ctx.fill();}}
 // 눈썹
 function brow(x){
  ctx.beginPath();
  if(c.brows==='straight'){ctx.moveTo(x-30,261);ctx.lineTo(x+30,261);}
  else if(c.brows==='arched'){ctx.moveTo(x-31,266);ctx.quadraticCurveTo(x,238,x+30,263);}
  else{ctx.moveTo(x-30,262);ctx.quadraticCurveTo(x-4,251,x+31,263);}
  ctx.lineWidth=7;ctx.strokeStyle=lighten(c.hairColor,-4);ctx.lineCap='round';ctx.stroke();
 }
 brow(390);brow(510);
 function eye(x,left){
  if(c.eyes==='smile'||(c.eyes==='wink'&&!left)){
   ctx.beginPath();ctx.moveTo(x-27,294);ctx.quadraticCurveTo(x,314,x+27,294);ctx.strokeStyle=INK;ctx.lineWidth=6;ctx.stroke();return;
  }
  const ey=c.eyes==='round'?25:c.eyes==='sharp'?15:21;
  ell(ctx,x,302,34,ey,'#FFFFFF',INK,4);
  ell(ctx,x+3,303,c.eyes==='round'?15:12,15,c.iris,null);
  ell(ctx,x+3,303,6,9,'#1C2235',null);
  ell(ctx,x-1,296,5,5,'#FFFFFF',null);
  if(c.eyes==='sharp')line(ctx,[[x+23,292],[x+39,284]],INK,4);
 }
 eye(390,true);eye(510,false);
 // 코
 paint(ctx,p=>{p.moveTo(451,313);p.quadraticCurveTo(445,340,461,346);},null,shadow,4);
 // 입
 if(c.mouth==='smile'){
  paint(ctx,p=>{p.moveTo(411,365);p.quadraticCurveTo(449,393,488,365);},null,'#9D4D56',6);
 }else if(c.mouth==='happy'){
  paint(ctx,p=>{p.moveTo(408,363);p.quadraticCurveTo(450,413,491,363);p.quadraticCurveTo(451,382,408,363);p.closePath();},'#A64E66','#8E435C',4);
  line(ctx,[[426,380],[475,380]],'#FFF4EE',4);
 }else if(c.mouth==='neutral')line(ctx,[[429,376],[474,376]],'#9D4D56',5);
 else ell(ctx,450,371,13,19,'#A85066','#8E435C',3);
 drawHairFront(ctx,c);
 drawGlasses(ctx,c);
 drawEarrings(ctx,c);
 drawHat(ctx,c);
 ctx.restore();
}
function drawHairFront(ctx,c){
 const b=c.hairColor;
 if(c.hairStyle==='spiky'){
  paint(ctx,p=>{p.moveTo(324,249);p.lineTo(296,162);p.lineTo(361,181);p.lineTo(354,112);p.lineTo(416,151);p.lineTo(469,93);p.lineTo(491,149);p.lineTo(548,102);p.lineTo(552,176);p.lineTo(604,163);p.lineTo(576,251);p.bezierCurveTo(538,221,519,219,484,203);p.quadraticCurveTo(400,258,324,249);p.closePath();},b);
 }else if(c.hairStyle==='curly'){
  for(const [x,y,r] of [[330,200,50],[366,160,56],[424,149,52],[478,149,54],[532,161,52],[570,208,53]])ell(ctx,x,y,r,r*.83,b);
 }else{
  paint(ctx,p=>{p.moveTo(316,249);p.bezierCurveTo(298,168,331,125,388,121);p.bezierCurveTo(451,96,532,109,569,148);p.bezierCurveTo(601,181,594,241,576,258);p.bezierCurveTo(554,230,540,199,535,190);p.bezierCurveTo(498,231,435,246,390,224);p.bezierCurveTo(366,250,333,257,316,249);p.closePath();},b);
  if(c.hairStyle==='long'||c.hairStyle==='bob'){
   line(ctx,[[356,180],[351,255]],lighten(b,18),7);
  }
 }
 if(c.hairStyle==='bun')ell(ctx,454,126,87,65,b);
 if(c.hairStyle==='ponytail')ell(ctx,590,177,34,23,lighten(b,12));
 ctx.lineWidth=5;ctx.strokeStyle=lighten(b,36);ctx.lineCap='round';ctx.beginPath();ctx.moveTo(366,182);ctx.quadraticCurveTo(431,135,490,155);ctx.stroke();
}
function drawGlasses(ctx,c){
 if(c.glasses==='none')return;
 const col=c.glasses==='sunglasses'?'#293448':c.accColor;
 const isRound=c.glasses==='round';
 ctx.save();ctx.lineWidth=7;ctx.strokeStyle=col;
 for(const x of [390,510]){
  ctx.beginPath();
  if(isRound)ctx.ellipse(x,301,49,39,0,0,Math.PI*2);
  else ctx.roundRect(x-52,267,104,70,14);
  if(c.glasses==='sunglasses'){ctx.fillStyle='#333B54D9';ctx.fill();}
  else{ctx.fillStyle='#C6E7FA42';ctx.fill();}
  ctx.stroke();
 }
 line(ctx,[[439,295],[460,295]],col,7);
 line(ctx,[[335,283],[307,277]],col,7);
 line(ctx,[[564,283],[590,277]],col,7);
 ctx.restore();
}
function drawEarrings(ctx,c){
 if(c.earrings==='none')return;
 for(const x of [303,597]){
  if(c.earrings==='stud')ell(ctx,x,355,11,11,c.accColor,lighten(c.accColor,-42),2);
  else {ctx.beginPath();ctx.ellipse(x,370,21,29,0,0,Math.PI*2);ctx.strokeStyle=c.accColor;ctx.lineWidth=9;ctx.stroke();}
 }
}
function drawHat(ctx,c){
 if(c.hat==='none')return;
 const a=c.accColor;
 if(c.hat==='cap'){
  paint(ctx,p=>{p.moveTo(318,184);p.bezierCurveTo(326,76,549,83,573,175);p.closePath();},a);
  paint(ctx,p=>{p.moveTo(321,188);p.quadraticCurveTo(441,146,575,184);p.quadraticCurveTo(556,211,344,216);p.closePath();},lighten(a,-12));
  line(ctx,[[448,112],[449,178]],lighten(a,-22),4);
 }else if(c.hat==='beanie'){
  paint(ctx,p=>{p.moveTo(321,220);p.bezierCurveTo(302,123,365,76,449,77);p.bezierCurveTo(541,75,608,129,577,222);p.closePath();},a);
  rect(ctx,319,194,260,46,18,lighten(a,-8));
 }else if(c.hat==='beret'){
  paint(ctx,p=>{p.moveTo(343,205);p.bezierCurveTo(282,163,355,83,449,94);p.bezierCurveTo(551,84,610,128,584,181);p.quadraticCurveTo(441,219,343,205);p.closePath();},a);
  line(ctx,[[442,105],[450,79]],lighten(a,-30),8);
 }else if(c.hat==='headband'){
  paint(ctx,p=>{p.moveTo(318,214);p.quadraticCurveTo(441,135,585,212);p.lineTo(587,233);p.quadraticCurveTo(441,157,320,233);p.closePath();},a);
 }
}
function torso(ctx,c){
 const top=c.topColor;
 if(c.top==='hoodie'){
  paint(ctx,p=>{p.moveTo(359,461);p.quadraticCurveTo(450,385,539,461);p.lineTo(537,549);p.quadraticCurveTo(450,521,364,549);p.closePath();},lighten(top,-28));
 }
 paint(ctx,p=>{p.moveTo(334,449);p.quadraticCurveTo(450,416,566,449);p.lineTo(582,681);p.quadraticCurveTo(454,711,318,682);p.closePath();},top);
 // 상의 스타일별 디테일
 if(c.top==='tshirt'){
  paint(ctx,p=>{p.moveTo(402,439);p.quadraticCurveTo(450,478,498,439);},null,lighten(top,-37),5);
  line(ctx,[[338,661],[565,661]],lighten(top,-20),3);
 }else if(c.top==='shirt'){
  paint(ctx,p=>{p.moveTo(397,434);p.lineTo(451,497);p.lineTo(479,445);p.lineTo(451,456);p.closePath();},'#FCFDFF');
  paint(ctx,p=>{p.moveTo(506,438);p.lineTo(450,497);p.lineTo(421,450);p.lineTo(451,458);p.closePath();},'#FCFDFF');
  line(ctx,[[450,497],[450,682]],lighten(top,-42),4);
  for(let y=527;y<=645;y+=37)ell(ctx,450,y,5,5,lighten(top,-66),null);
 }else if(c.top==='jacket'){
  paint(ctx,p=>{p.moveTo(346,445);p.lineTo(431,458);p.lineTo(449,695);p.lineTo(316,676);p.closePath();},lighten(top,-12));
  paint(ctx,p=>{p.moveTo(553,445);p.lineTo(465,458);p.lineTo(451,695);p.lineTo(583,677);p.closePath();},lighten(top,7));
  line(ctx,[[450,466],[449,684]],'#D4DAEA',5);
  line(ctx,[[384,525],[425,525]],lighten(top,-45),5);
 }else if(c.top==='hoodie'){
  paint(ctx,p=>{p.moveTo(402,438);p.quadraticCurveTo(451,490,497,438);},null,lighten(top,-38),6);
  line(ctx,[[418,461],[412,540]],'#F9EFF0',5);line(ctx,[[480,460],[486,540]],'#F9EFF0',5);
  rect(ctx,390,576,119,70,18,lighten(top,-16),null);
 }else if(c.top==='sweater'){
  for(let i=0;i<8;i++)line(ctx,[[330+i*32,666],[330+i*32,681]],lighten(top,-30),3);
  paint(ctx,p=>{p.moveTo(405,442);p.quadraticCurveTo(450,479,496,442);},null,lighten(top,-40),12);
 }
}
function bagAndNecklace(ctx,c){
 if(c.bag==='backpack'){
  // 어깨 뒤에서 앞으로 가방 끈이 보이게
  paint(ctx,p=>{p.moveTo(347,470);p.lineTo(369,470);p.lineTo(393,675);p.lineTo(369,677);p.closePath();},lighten(c.accColor,-15));
  paint(ctx,p=>{p.moveTo(529,470);p.lineTo(551,470);p.lineTo(527,679);p.lineTo(505,679);p.closePath();},lighten(c.accColor,-15));
 }else if(c.bag==='crossbody'){
  ctx.beginPath();ctx.moveTo(364,461);ctx.quadraticCurveTo(483,582,551,734);ctx.strokeStyle=lighten(c.accColor,-37);ctx.lineWidth=23;ctx.stroke();
  rect(ctx,495,678,120,127,25,c.accColor);rect(ctx,518,689,82,25,10,lighten(c.accColor,-22),null);
 }
 if(c.necklace!=='none'){
  ctx.beginPath();ctx.moveTo(411,452);ctx.quadraticCurveTo(450,533,489,452);ctx.strokeStyle=c.accColor;ctx.lineWidth=6;ctx.stroke();
  if(c.necklace==='pendant')ell(ctx,451,521,16,20,c.accColor,lighten(c.accColor,-30),3);
 }
}
function drawAvatar(ctx,c,width=900,height=1100){
 if(!ctx)return;
 ctx.save();ctx.clearRect(0,0,width,height);ctx.scale(width/900,height/1100);
 const profiles={standard:[1,1,1],petite:[.92,.93,1.08],tall:[.94,1.035,.96],broad:[1.10,1,1]};
 const [sw,sh,headExtra]=profiles[c.bodyType]||profiles.standard;
 ctx.translate(450,580);ctx.scale(sw,sh);ctx.translate(-450,-580);
 // 다리와 팔 -> 목 -> 상의 -> 얼굴의 순서로 레이어 처리
 legs(ctx,c);arm(ctx,c,'left');arm(ctx,c,'right');
 rect(ctx,419,393,62,85,25,c.skin);
 torso(ctx,c);
 bagAndNecklace(ctx,c);
 ctx.save();ctx.translate(450,300);ctx.scale(headExtra,headExtra);ctx.translate(-450,-300);drawFace(ctx,c);ctx.restore();
 ctx.restore();
}

// ---------- 상태/입력/프리셋 ----------
function normalized(input){
 if(!input||typeof input!=='object')throw new Error('JSON 설정이 올바르지 않습니다.');
 const out={...base};
 for(const key of fields){
  const val=input[key];if(val===undefined)continue;
  if(key==='avatarName'){out[key]=String(val).replace(/[\r\n<>]/g,'').slice(0,24)||'나의 아바타';continue;}
  if(key==='freckles'){out[key]=!!val;continue;}
  if(COLORS.includes(key)){if(typeof val==='string'&&/^#[0-9a-fA-F]{6}$/.test(val))out[key]=val.toUpperCase();continue;}
  if(selectValues[key]?.includes(val))out[key]=val;
 }
 return out;
}
function writeControls(){for(const key of fields){const node=$(key);if(!node)continue;if(key==='freckles')node.checked=!!state[key];else node.value=state[key];}}
function readControl(key){const node=$(key);if(!node)return;if(key==='freckles')state[key]=node.checked;else if(key==='avatarName')state[key]=node.value;else state[key]=node.value;}
function createThumbs(){const box=$('presetGrid');box.innerHTML='';for(const t of templates){const b=document.createElement('button');b.type='button';b.className='preset-card';b.dataset.preset=t.id;const canvas=document.createElement('canvas');canvas.width=270;canvas.height=330;canvas.setAttribute('aria-hidden','true');drawAvatar(canvas.getContext('2d'),t.set,270,330);const span=document.createElement('span');span.textContent=t.name;b.append(canvas,span);b.addEventListener('click',()=>{setState(t.set,t.id);toast(t.name+' 프리셋을 선택했습니다.');});box.append(b);}}
function toast(message){const node=$('toast');if(!node)return;node.textContent=message;node.style.display='block';if(toastTimer)clearTimeout(toastTimer);toastTimer=setTimeout(()=>{node.style.display='none';},3600);}
function setState(next,preset=null){state=normalized(next);chosen=preset;writeControls();redraw();}
function redraw(){
 drawAvatar(avatarCtx,state);
 if(three){three.texture.needsUpdate=true;three.renderer.render(three.scene,three.camera);}
 $('displayName').textContent=state.avatarName||'나의 아바타';$('detailsName').textContent=state.avatarName||'나의 아바타';
 $('detailsTags').replaceChildren(...[
  captions.face[state.face],captions.hairStyle[state.hairStyle],captions.top[state.top],captions.bottom[state.bottom]
 ].map(str=>{const s=document.createElement('span');s.textContent=str;return s;}));
 $('displayDesc').textContent=`${captions.hairStyle[state.hairStyle]} · ${captions.top[state.top]} · ${captions.bottom[state.bottom]}`;
 for(const k of COLORS){const el=$(k+'Value');if(el)el.textContent=state[k].toUpperCase();}
 for(const b of document.querySelectorAll('[data-preset]')){b.classList.toggle('selected',b.dataset.preset===chosen);}
}
function randomize(){const pick=list=>list[Math.floor(Math.random()*list.length)];const palettes=['#5E81EA','#F17887','#4BB79C','#FEA343','#9B76C7','#253F58'];const skins=['#F2D0BB','#EAB48E','#D39A75','#AB7456','#76503E'];const hairs=['#271D29','#4F3025','#8E5735','#C49A52','#6C427D'];
 const obj={...base,avatarName:'랜덤 아바타'};
 for(const key of Object.keys(selectValues))obj[key]=pick(selectValues[key]);
 obj.skin=pick(skins);obj.hairColor=pick(hairs);obj.topColor=pick(palettes);obj.bottomColor=pick(palettes);obj.shoeColor=pick(['#F6F8FF','#2D3547','#DEA36E']);obj.iris=pick(['#41322B','#2B5A60','#60462E']);obj.accColor=pick(['#E9B949','#DB9DDB','#91BCEF']);obj.freckles=Math.random()<.22;
 setState(obj,null);toast('새로운 아바타를 랜덤 생성했습니다.');
}
function download(blob,name){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
function fileBase(){return String(state.avatarName||'avatar').trim().replace(/[^\w가-힣-]/g,'_').slice(0,26)||'avatar';}
function exportPng(){avatarCanvas.toBlob(blob=>{if(!blob){toast('PNG 이미지 생성에 실패했습니다.');return;}download(blob,`avatar_${fileBase()}.png`);toast('투명 배경 PNG를 저장했습니다.');},'image/png');}
function saveLocal(){try{localStorage.setItem('avatar2d-threejs-settings-v2',JSON.stringify(state));toast('브라우저에 아바타를 저장했습니다.');}catch(e){toast('이 브라우저에서는 로컬 저장을 사용할 수 없습니다. JSON 저장을 사용하세요.');}}
function loadLocal(){try{const json=localStorage.getItem('avatar2d-threejs-settings-v2');if(!json){toast('저장된 아바타가 없습니다.');return;}setState(JSON.parse(json));toast('저장된 아바타를 불러왔습니다.');}catch(e){toast('저장된 데이터를 불러오지 못했습니다.');}}
function exportJson(){download(new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),`avatar_${fileBase()}.json`);toast('아바타 설정을 JSON으로 저장했습니다.');}
async function importJson(file){try{const raw=await file.text();const cfg=JSON.parse(raw);setState(cfg);toast('JSON에서 아바타를 복원했습니다.');}catch(e){toast('유효한 JSON 아바타 설정 파일을 선택해 주세요.');}}
function setupUI(){
 createThumbs();writeControls();redraw();
 document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t===tab));document.querySelectorAll('.tab-panel').forEach(p=>p.classList.toggle('active',p.dataset.panel===tab.dataset.tab));}));
 for(const key of fields){const el=$(key);if(!el)continue;el.addEventListener(key==='avatarName'?'input':key==='freckles'?'change':'input',()=>{readControl(key);chosen=null;redraw();});}
 $('randomBtn').addEventListener('click',randomize);$('resetBtn').addEventListener('click',()=>{setState(base,'sky');toast('기본 아바타로 되돌렸습니다.');});
 $('savePngBtn').addEventListener('click',exportPng);$('sidePngBtn').addEventListener('click',exportPng);
 $('saveLocalBtn').addEventListener('click',saveLocal);$('loadLocalBtn').addEventListener('click',loadLocal);
 $('exportJsonBtn').addEventListener('click',exportJson);$('importJsonBtn').addEventListener('click',()=>$('jsonInput').click());
 $('jsonInput').addEventListener('change',async(e)=>{const f=e.target.files?.[0];if(f)await importJson(f);e.target.value='';});
 const applyZoom=()=>{$('artSurface').style.transform=`scale(${zoom})`;$('zoomText').textContent=Math.round(zoom*100)+'%';};
 $('zoomIn').onclick=()=>{zoom=Math.min(1.4,Math.round((zoom+.1)*10)/10);applyZoom();};
 $('zoomOut').onclick=()=>{zoom=Math.max(.7,Math.round((zoom-.1)*10)/10);applyZoom();};
}

// ---------- 로컬 Three.js (UMD r149) 연결 ----------
// 기존 코드의 r160 build/three.min.js + examples/js/controls/... 경로는 제공되지 않아 렌더링이 실패했습니다.
// 이 파일은 OrbitControls가 필요 없는 2D 정사영 구현이므로 라이브러리 하나만 있으면 됩니다.
function activateThree(){
 const THREE=window.THREE;if(!THREE||!THREE.OrthographicCamera||three)return false;
 try{
  const holder=$('artSurface');
  const scene=new THREE.Scene();
  const camera=new THREE.OrthographicCamera(-1,1,1100/900,-1100/900,.1,10);
  camera.position.z=3;camera.lookAt(0,0,0);
  const texture=new THREE.CanvasTexture(avatarCanvas);texture.needsUpdate=true;
  texture.minFilter=THREE.LinearFilter;texture.magFilter=THREE.LinearFilter;
  const mat=new THREE.MeshBasicMaterial({map:texture,transparent:true,side:THREE.DoubleSide,depthWrite:false});
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(2,2*1100/900),mat);scene.add(mesh);
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,premultipliedAlpha:false});
  renderer.setClearColor(0x000000,0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.setSize(900,1100,false);
  renderer.domElement.id='threeCanvas';renderer.domElement.setAttribute('aria-label','Three.js 정사영 2D 아바타');renderer.domElement.style.pointerEvents='none';
  holder.appendChild(renderer.domElement);renderer.render(scene,camera);
  three={texture,renderer,scene,camera};
  $('renderStatus').innerHTML='<span class="dot"></span> Three.js 정사영 2D';
  return true;
 }catch(e){console.warn('Three.js 전환 실패 — Canvas 2D 유지',e);const el=$('threeCanvas');if(el)el.remove();return false;}
}
function loadThreeSource(src,onDone,onFail){const script=document.createElement('script');script.src=src;script.async=true;script.onload=()=>{if(!activateThree())onFail?.();else onDone?.();};script.onerror=()=>{script.remove();onFail?.();};document.head.appendChild(script);}
function tryThree(){
 // 현재 폴더 또는 HTML 옆 vendor/three.min.js (Node downloader로 준비)
 loadThreeSource('vendor/three.min.js',null,()=>{
  // CDN 로드에 실패해도 Canvas 아바타는 계속 보입니다.
  loadThreeSource('https://cdn.jsdelivr.net/npm/three@0.149.0/build/three.min.js',null,()=>{
   $('renderStatus').innerHTML='<span class="dot"></span> HTML5 2D (오프라인)';
  });
 });
}
setupUI();tryThree();
})();

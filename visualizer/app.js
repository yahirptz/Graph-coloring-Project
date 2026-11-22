"use strict";

// We send the canvas adjacency matrix to /api/solve, which uses the same solver as the CLI.
const svg = document.getElementById("graph-svg");
const nodesLayer = document.getElementById("nodes-layer");
const edgesLayer = document.getElementById("edges-layer");
const colors = ["#5794fb", "#f87182", "#f4c86b", "#4bc99c", "#f39262", "#a895f8", "#56cbd6", "#e47bbb", "#bca48c", "#ed99bc"];
const names = ["Blue", "Red", "Yellow", "Green", "Orange", "Purple", "Cyan", "Magenta", "Brown", "Pink"];
const hints = {add:"Click empty space to add a vertex",connect:"Click two vertices to toggle an edge",move:"Drag a vertex to reposition it",delete:"Click a vertex or an edge to delete"};
const $ = id => document.getElementById(id);
let vertices = [], edgeKeys = new Set(), mode = "add", startConnection = null, drag = null;
let solution = null, step = 0, playTimer = null, solving = false, revision = 0;
let loadVersion = 0;
const incidentLines = new Map();
const MAX_VERTICES = 80;
const NS = "http://www.w3.org/2000/svg";

function node(tag, attrs) { const el=document.createElementNS(NS,tag); for (const [k,v] of Object.entries(attrs||{})) el.setAttribute(k,v); return el; }
function key(a,b) {return `${Math.min(a,b)}-${Math.max(a,b)}`;}
function edgePair(edge) {return edge.split("-").map(Number);}
function matrixOf() {const n=vertices.length, m=Array.from({length:n},()=>Array(n).fill(0)); for(const e of edgeKeys){const[a,b]=edgePair(e);m[a-1][b-1]=1;m[b-1][a-1]=1;}return m;}
function status(message, state="") {const el=$("status");el.className=`status ${state}`;el.innerHTML="";const dot=document.createElement("span");dot.className="status-dot";el.append(dot,document.createTextNode(message));}
function groupColor(index) {
  return colors[index] || `hsl(${(index * 137.508) % 360} 62% ${[65, 78, 88][index % 3]}%)`;
}
function groupName(index) { return names[index] || `Color ${index + 1}`; }
function vertexRadius() {
  return Math.max(14, Math.min(20, 120 / Math.sqrt(Math.max(1, vertices.length))));
}
function stopPlay(){if(playTimer!==null){clearInterval(playTimer);playTimer=null;}$("play-step").textContent="▶ Play";}
function invalidate(){revision++;loadVersion++;solution=null;step=0;stopPlay();$("result-badge").textContent="NOT SOLVED";$("result-badge").className="result-badge";$("sequence").innerHTML='<span class="placeholder">Graph changed. Run the solver to refresh.</span>';$("groups").replaceChildren();$("balance").textContent="";$("playback").hidden=true;}
function setMode(next){drag=null;mode=next;startConnection=null;document.querySelectorAll(".tool").forEach(el=>{const active=el.dataset.tool===next;el.classList.toggle("active",active);el.setAttribute("aria-pressed",active);});$("mode-hint").textContent=hints[next];renderGraph();}
function coordinates(event){const pt=svg.createSVGPoint();pt.x=event.clientX;pt.y=event.clientY;const transform=svg.getScreenCTM();if(!transform)return {x:400,y:255};const p=pt.matrixTransform(transform.inverse());return {x:Math.max(27,Math.min(773,p.x)),y:Math.max(27,Math.min(483,p.y))};}
function moveCount(){ $("vertex-count").textContent=vertices.length;$("edge-count").textContent=edgeKeys.size; }
function addVertex(x,y){if(vertices.length>=MAX_VERTICES){status("Maximum 80 vertices in the visual editor.","error");return;}vertices.push({id:vertices.length+1,x,y});invalidate();renderAll();status(`Added vertex ${vertices.length}.`,"success");}
function deleteVertex(id){vertices=vertices.filter(v=>v.id!==id);for(const v of vertices)if(v.id>id)v.id--;
 edgeKeys=new Set([...edgeKeys].flatMap(e=>{let[a,b]=edgePair(e);if(a===id||b===id)return [];if(a>id)a--;if(b>id)b--;return [key(a,b)];}));startConnection=null;invalidate();renderAll();status(`Deleted vertex ${id}.`,"success");}
function toggleEdge(a,b){if(a===b){renderGraph();status("Self-loops are not allowed.","error");return;}const e=key(a,b);if(edgeKeys.has(e)){edgeKeys.delete(e);status(`Removed edge ${a}–${b}.`,"success");}else{edgeKeys.add(e);status(`Connected vertex ${a} to ${b}.`,"success");}invalidate();renderAll();}
function handleVertex(id,event){event.stopPropagation();if(mode==="connect"){if(startConnection===null){startConnection=id;status(`Selected vertex ${id}. Now select a second vertex.`);renderGraph();}else{const start=startConnection;startConnection=null;toggleEdge(start,id);}} else if(mode==="delete")deleteVertex(id);}
function renderGraph() {
  nodesLayer.replaceChildren();
  edgesLayer.replaceChildren();
  incidentLines.clear();
  const colorByVertex = new Map();
  solution?.groups?.forEach((group, index) => {
    group.forEach(id => colorByVertex.set(id, index));
  });
  const radius = vertexRadius();

  for (const edge of edgeKeys) {
    const [a, b] = edgePair(edge);
    const [first, second] = [vertices[a - 1], vertices[b - 1]];
    const attrs = {x1: first.x, y1: first.y, x2: second.x, y2: second.y};
    const line = node("line", {...attrs, class: "graph-edge"});
    const hit = node("line", {...attrs, class: "edge-hit"});
    hit.addEventListener("click", event => {
      if (mode !== "delete") return;
      event.stopPropagation();
      edgeKeys.delete(edge);
      invalidate();
      renderAll();
      status(`Deleted edge ${a}–${b}.`, "success");
    });
    for (const [id, end] of [[a, 1], [b, 2]]) {
      if (!incidentLines.has(id)) incidentLines.set(id, []);
      incidentLines.get(id).push({line, hit, end});
    }
    edgesLayer.append(line, hit);
  }

  for (const vertex of vertices) {
    const {id, x, y} = vertex;
    const index = id <= step ? colorByVertex.get(id) : undefined;
    const fill = index === undefined ? "#ffffff" : groupColor(index);
    const selected = id === startConnection ? " selected" : "";
    const group = node("g", {class: "node-wrapper" + selected, "data-id": id});
    const title = node("title");
    title.textContent = index === undefined ? `Vertex ${id}` : `Vertex ${id} · ${groupName(index)}`;
    const circle = node("circle", {cx: x, cy: y, r: radius, fill, class: "graph-node"});
    const label = node("text", {x, y: y + 1, class: "node-label"});
    label.textContent = id;
    group.append(title, circle, label);
    group.addEventListener("click", event => handleVertex(id, event));
    group.addEventListener("pointerdown", event => {
      if (mode !== "move" || drag || event.button !== 0) return;
      event.preventDefault();
      svg.setPointerCapture(event.pointerId);
      drag = {id, pointerId: event.pointerId};
    });
    nodesLayer.append(group);
  }
}

svg.addEventListener("pointermove", event => {
  if (!drag || drag.pointerId !== event.pointerId) return;
  const vertex = vertices[drag.id - 1];
  const group = nodesLayer.querySelector(`[data-id="${drag.id}"]`);
  if (!vertex || !group) return;
  const {x, y} = coordinates(event);
  Object.assign(vertex, {x, y});
  const circle = group.querySelector("circle");
  const label = group.querySelector("text");
  circle.setAttribute("cx", x);
  circle.setAttribute("cy", y);
  label.setAttribute("x", x);
  label.setAttribute("y", y + 1);
  for (const {line, hit, end} of incidentLines.get(vertex.id) || []) {
    for (const element of [line, hit]) {
      element.setAttribute(`x${end}`, x);
      element.setAttribute(`y${end}`, y);
    }
  }
});
svg.addEventListener("lostpointercapture", event => {
  if (drag?.pointerId === event.pointerId) drag = null;
});
svg.addEventListener("click",ev=>{if(mode==="add"&&(ev.target===svg||ev.target.classList.contains("canvas-bg"))){const {x,y}=coordinates(ev);addVertex(x,y);}});
function renderMatrix(){const container=$("matrix-preview");container.replaceChildren();if(!vertices.length){container.textContent="Add a vertex to display its adjacency matrix.";return;}const m=matrixOf(),table=document.createElement("table");table.className="matrix";const header=table.insertRow();header.appendChild(document.createElement("th"));for(let j=0;j<m.length;j++){const cell=document.createElement("th");cell.textContent=j+1;header.appendChild(cell);}m.forEach((row,i)=>{const tr=table.insertRow();const th=document.createElement("th");th.textContent=i+1;tr.append(th);row.forEach((v,j)=>{const td=tr.insertCell();td.textContent=v;td.className=i===j?"diag":v?"one":"";});});container.append(table);}
function renderAll(){moveCount();renderMatrix();renderGraph();}
function constructPositions(n){
 if (n === 1) return [{id: 1, x: 400, y: 255}];
 if (n > 24) {
   const columns = Math.ceil(Math.sqrt(n * 1.55));
   const rows = Math.ceil(n / columns);
   return Array.from({length: n}, (_, i) => ({
     id: i + 1,
     x: 65 + (i % columns) * 670 / (columns - 1),
     y: 50 + Math.floor(i / columns) * 410 / (rows - 1),
   }));
 }
let out=[];const radius=n<=3?140:n<=12?188:207;for(let i=0;i<n;i++){const angle=-Math.PI/2+i*2*Math.PI/n;out.push({id:i+1,x:400+Math.cos(angle)*radius,y:255+Math.sin(angle)*radius});}return out;}
function applyGraph(k,matrix){drag=null;vertices=constructPositions(matrix.length);edgeKeys=new Set();for(let i=0;i<matrix.length;i++)for(let j=i+1;j<matrix.length;j++)if(matrix[i][j])edgeKeys.add(key(i+1,j+1));$("k-input").value=k;startConnection=null;invalidate();renderAll();}
async function loadExample(name){const version=++loadVersion;try{const response=await fetch(`/api/example?name=${encodeURIComponent(name)}`);const data=await response.json();if(!response.ok)throw Error(data.error||"Cannot load sample.");if(version!==loadVersion)return;applyGraph(data.k,data.matrix);setMode("add");status("Example loaded.","success");}catch(e){if(version===loadVersion)status(e.message,"error");}}
function displayResult(data){solution=data;stopPlay();const badge=$("result-badge");if(!data.possible){badge.className="result-badge invalid";badge.textContent="IMPOSSIBLE";$("sequence").textContent="No valid coloring";$("balance").textContent=data.text;$("groups").replaceChildren();$("playback").hidden=true;step=0;renderGraph();status("No coloring using exactly k nonempty colors exists.","error");return;}
 badge.className="result-badge valid";badge.textContent="OPTIMAL";$("sequence").textContent=`(${data.sequence.join(",")})`;$("balance").textContent=`Minimum class-size difference: ${data.imbalance}`;const list=$("groups");list.replaceChildren();data.groups.forEach((group,i)=>{const row=document.createElement("div");row.className="group";const swatch=document.createElement("span");swatch.className="swatch";swatch.style.background=groupColor(i);const name=document.createElement("strong");name.className="group-name";name.textContent=groupName(i);const number=document.createElement("span");number.className="group-number";number.textContent=group.join(", ");row.append(swatch,name,number);list.append(row);});$("playback").hidden=false;step=vertices.length;$("step-slider").max=vertices.length;updateStep();status("Optimal coloring found.","success");}
function updateStep(){if(!solution?.possible)return;$("step-slider").value=step;$("step-label").textContent=`${step} / ${vertices.length}`;renderGraph();}
function parseInput(text){const rows=text.trim().split(/\r?\n/).map(s=>s.trim()).filter(Boolean);if(rows.length<3)throw Error("File must contain k, n, then n adjacency rows.");if(!rows.slice(0,2).every(row=>/^\+?\d+$/.test(row)))throw Error("k and n must be positive integers.");const k=Number(rows[0]),n=Number(rows[1]);if(!Number.isSafeInteger(k)||k<1||!Number.isInteger(n)||n<1||n>MAX_VERTICES)throw Error("k and n must be positive integers (maximum 80 vertices).");if(rows.length!==n+2)throw Error(`Expected ${n} adjacency rows but found ${rows.length-2}.`);const matrix=rows.slice(2).map((row,i)=>{const tokens=row.split(/\s+/);if(tokens.length!==n||tokens.some(t=>t!=="0"&&t!=="1"))throw Error(`Row ${i+1} must have ${n} space-separated zeros and ones.`);return tokens.map(Number);});for(let i=0;i<n;i++){if(matrix[i][i]!==0)throw Error("Self-loops are not allowed.");for(let j=0;j<n;j++)if(matrix[i][j]!==matrix[j][i])throw Error("The matrix must be symmetric.");}return {k,matrix};}
async function solve(){if(solving)return;stopPlay();const k=Number($("k-input").value);if(!Number.isSafeInteger(k)||k<1){status("Enter a positive integer for k.","error");return;}if(!vertices.length){status("Add at least one vertex first.","error");return;}
 const startedAt=revision;solving=true;$("solve-btn").disabled=true;$("solve-label").textContent="Searching for an exact solution…";status("Finding a coloring…");try{const res=await fetch("/api/solve",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({k,matrix:matrixOf()})});const data=await res.json();if(startedAt!==revision){status("Graph changed during the calculation; solve again.");return;}if(!res.ok)throw Error(data.error||"Solver error.");displayResult(data);}catch(e){if(startedAt===revision){invalidate();status(e.message,"error");}}finally{solving=false;$("solve-btn").disabled=false;$("solve-label").textContent="Find optimal coloring";}}
function exportInput(){const k=Number($("k-input").value);if(!Number.isSafeInteger(k)||k<1){status("Enter a positive integer for k.","error");return;}if(!vertices.length){status("Add a vertex before exporting.","error");return;}const m=matrixOf();const text=[k,vertices.length,...m.map(row=>row.join(" "))].join("\n")+"\n";const blob=new Blob([text],{type:"text/plain"});const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download="graph_input.txt";link.click();setTimeout(()=>URL.revokeObjectURL(url),1500);status("Exported graph_input.txt.","success");}
document.querySelectorAll(".tool").forEach(el=>el.addEventListener("click",()=>setMode(el.dataset.tool)));
$("k-plus").addEventListener("click",()=>{$("k-input").value=Math.max(1,Number($("k-input").value||0)+1);invalidate();renderGraph();});
$("k-minus").addEventListener("click",()=>{$("k-input").value=Math.max(1,Number($("k-input").value||0)-1);invalidate();renderGraph();});
$("k-input").addEventListener("input",()=>{invalidate();renderGraph();});
$("solve-btn").addEventListener("click",solve);
$("sample-list").addEventListener("change",ev=>loadExample(ev.target.value));
$("reset-example").addEventListener("click",()=>loadExample($("sample-list").value));
$("clear-graph").addEventListener("click",()=>{vertices=[];edgeKeys.clear();startConnection=null;drag=null;invalidate();renderAll();status("Graph cleared.");});
$("export-file").addEventListener("click",exportInput);
$("import-button").addEventListener("click", () => $("import-file").click());
$("import-file").addEventListener("change", async event => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  const version = ++loadVersion;
  try {
    const parsed = parseInput(await file.text());
    if (version !== loadVersion) return;
    applyGraph(parsed.k, parsed.matrix);
    status(`Imported ${file.name}.`, "success");
  } catch (error) {
    if (version === loadVersion) status(error.message, "error");
  }
});
$("step-slider").addEventListener("input",ev=>{stopPlay();step=Number(ev.target.value);updateStep();});
$("prev-step").addEventListener("click",()=>{stopPlay();step=Math.max(0,step-1);updateStep();});
$("next-step").addEventListener("click",()=>{stopPlay();step=Math.min(vertices.length,step+1);updateStep();});
$("play-step").addEventListener("click",()=>{if(playTimer!==null){stopPlay();return;}if(step>=vertices.length)step=0;updateStep();$("play-step").textContent="Ⅱ Pause";playTimer=setInterval(()=>{step++;updateStep();if(step>=vertices.length)stopPlay();},550);});
loadExample("example_k3");

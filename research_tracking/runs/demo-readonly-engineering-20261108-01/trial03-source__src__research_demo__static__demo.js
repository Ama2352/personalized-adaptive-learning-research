"use strict";
const $ = id => document.getElementById(id);
const labels = {graph_free:"Graph-free",graph_package:"Graph package đầy đủ",empty_graph_package:"Graph package rỗng (negative control)"};
let currentRequest = 0;
const node = (tag, text, className) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=String(text); if(className)n.className=className; return n; };
async function get(url){const r=await fetch(url,{cache:"no-store"});if(!r.ok)throw new Error("Không đọc được dữ liệu đã kiểm: HTTP "+r.status);return r.json();}
function fail(e){$("error").hidden=false;$("error").textContent=e.message;}
function option(id, values, display){for(const value of values){const o=node("option",display?display(value):value);o.value=String(value);$(id).append(o);}$(id).disabled=false;}
function tableRow(id, values){const row=node("tr");for(const value of values)row.append(node("td",value));$(id).append(row);}
function stepTo(step){$("step").value=String(step);loadSnapshot().catch(fail);}
async function loadSnapshot(){const request=++currentRequest;const q=new URLSearchParams({profile:$("profile").value,seed:$("seed").value,variant:$("variant").value,step:$("step").value});const s=await get("/api/replay?"+q);if(request!==currentRequest)return;
 $("step-label").textContent=s.step+" / 119";$("previous").disabled=s.step===0;$("next").disabled=s.step===119;
 $("probability").textContent=s.p_correct_logged_query.toFixed(6);$("concept").textContent=s.concept_preview===null?"Không có concept preview":s.concept_preview;
 $("comparison").textContent="So với graph-free: scalar p "+(s.reference.p_changed_exact?"khác (so sánh exact)":"giữ nguyên")+"; concept preview "+(s.reference.preview_changed?"khác":"giữ nguyên")+".";
 $("baseline").textContent="Graph-free cùng snapshot: p = "+s.reference.p_correct_logged_query.toFixed(6)+"; preview = "+(s.reference.concept_preview??"không có")+".";
 $("concepts").replaceChildren();const ready=new Set(s.ready);for(const [concept, mastered] of Object.entries(s.mastered_bool)){const r=node("div",undefined,"concept-row");r.append(node("span",concept),node("span",mastered?"Đã đạt":"Chưa đạt","flag"+(mastered?" on":"")),node("span",ready.has(concept)?"Ready":"—","flag"+(ready.has(concept)?" on":"")));$("concepts").append(r);}
 $("route").replaceChildren();s.route_preview.forEach((concept,i)=>{const li=node("li");const b=node("button",i+" · "+(concept??"không có"));b.type="button";if(i===s.step)b.setAttribute("aria-current","step");b.addEventListener("click",()=>stepTo(i));li.append(b);$("route").append(li);});
}
async function init(){const c=await get("/api/catalog");option("profile",c.profiles);option("seed",c.seeds);option("variant",c.variants,v=>labels[v]||v);$("step").max=String(c.steps-1);$("step").disabled=false;$("coverage").textContent=c.profiles.length+" profile × "+c.seeds.length+" seed × "+c.variants.length+" variant × "+c.steps+" snapshot. Lựa chọn không tạo lượt mô phỏng mới.";
 for(const id of ["profile","seed","variant"])$(id).addEventListener("change",()=>loadSnapshot().catch(fail));$("step").addEventListener("input",()=>loadSnapshot().catch(fail));$("previous").addEventListener("click",()=>stepTo(Math.max(0,Number($("step").value)-1)));$("next").addEventListener("click",()=>stepTo(Math.min(c.steps-1,Number($("step").value)+1)));
 for(const r of c.rq1)tableRow("rq1",[labels[r.candidate],r.event_pairs,r.changed_probability_events,r.changed_mastery_events_any_concept,r.changed_ready_events,r.changed_action_preview_events]);
 $("rq1-takeaway").textContent="Graph package đầy đủ: 944/964 snapshot có P đổi nhưng concept preview giữ. Empty graph package: 37 P đổi, 0 mastery/ready/preview đổi. Package không đồng nghĩa riêng các cạnh.";
 for(const r of c.rq2_synthetic.profiles)tableRow("rq2",[r.profile,r.seed_blocks,r.mean_lambda_edge_interaction.toFixed(6),r.mechanism_exposed_events+" / "+r.mechanism_event_denominator]);
 const contrast=c.rq2_synthetic.paired_profile_contrasts.find(r=>r.contrast==="I(PYH)-I(PY)");if(contrast)$("rq2-takeaway").textContent="PYH − PY: mean "+contrast.mean.toFixed(6)+" Elo; "+contrast.signs.positive+" seed dương / "+contrast.signs.negative+" seed âm. Leave-one-seed-out mean ["+contrast.loo_min.toFixed(6)+", "+contrast.loo_max.toFixed(6)+"]. Thứ tự chưa ổn định; đây là sensitivity mô tả, không CI.";
 for(const m of c.models)$("models").append(node("dt",m.name),node("dd",m.status));for(const s of c.sources){const li=node("li");li.append(node("strong",s.run+" / "+s.file),node("div","Output SHA-256: "+s.sha256),node("div","Manifest SHA-256: "+s.manifest_sha256));$("sources").append(li);}for(const limit of c.limits_vi)$("limits").append(node("li",limit));await loadSnapshot();
}
init().catch(fail);

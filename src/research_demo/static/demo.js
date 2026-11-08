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
function showMode(closed){
 $("mode-lead").textContent=closed?"Closed loop / quyết định nguồn đã lưu":"Replay pilot / preview";
 $("replay-heading").textContent=closed?"Một quyết định đã phục vụ trong simulator":"Một snapshot trước cập nhật";
 $("boundary-title").textContent=closed?"Current-source reconstruction · post-hoc":"Ranh giới quan sát";
 $("boundary-primary").textContent=closed?"Actual served item của simulator, không người học thật. Nguyên runner lịch sử a585 vẫn thiếu; không backfill historical trace.":"Concept preview được tính trên bản sao trước cập nhật. Không phải action đã phục vụ cho người học.";
 $("boundary-query").textContent=closed?"M/R/C/B trước bookkeeping; P của served query được tính sau select. Package không đồng nghĩa riêng các cạnh.":"Trace không lưu item/question/timestamp; không gán xác suất hiện tại cho concept preview.";
 $("probability-title").textContent=closed?"p(correct) của served item · sau select":"p(correct) của logged query";
 $("probability-note").textContent=closed?"Scalar đã lưu sau lựa chọn, trước interact/update; không là đầu vào của same-step selection, không P(đã biết).":"Scalar đã lưu. Không phải xác suất concept preview; không phải P(đã biết).";
 $("concept-title").textContent=closed?"Item thực sự được phục vụ trong simulator":"Concept được preview";
 $("state-heading").textContent=closed?"M/R/C/B trước selector bookkeeping · 28 concepts":"Ready set và native mastery boolean · 28 concepts";
 $("state-note").textContent=closed?"M là native boolean; R ready, C eligible sau escape, B balanced. Không calibrated mastery. Selected thuộc B ⊆ C; không suy từ P hiện tại.":"“Đã đạt” là cờ native is_mastered đã lưu, không là latent mastery probability. Ready membership khác ranking lựa chọn.";
 $("route-heading").textContent=closed?"Chuỗi concept đã phục vụ đến bước đang xem":"Chuỗi concept preview đến bước đang xem";
 $("route-note").textContent=closed?"Mỗi mục là một bước timeline đã lưu, không số node của graph. Không gọi lại policy hoặc mô phỏng mới.":"Theo thứ tự snapshot trên fixed stream; không phải lộ trình action đã phục vụ. Mỗi mục đưa về một bước đã lưu.";
 $("closed-detail").hidden=!closed;
}
function renderConcepts(s,closed){
 $("concepts").replaceChildren();const ready=new Set(s.ready),candidates=new Set(s.candidates||[]),balanced=new Set(s.balanced||[]);
 for(const [concept,mastered] of Object.entries(s.mastered_bool)){const r=node("div",undefined,"concept-row");const membership=closed?[ready.has(concept)?"R":"—",candidates.has(concept)?"C":"—",balanced.has(concept)?"B":"—"].join(" / "):(ready.has(concept)?"Ready":"—");r.append(node("span",concept),node("span",mastered?"Đã đạt":"Chưa đạt","flag"+(mastered?" on":"")),node("span",membership,"flag"+(ready.has(concept)?" on":"")));$("concepts").append(r);}
}
function renderRoute(route,step){$("route").replaceChildren();route.forEach((concept,i)=>{const li=node("li");const b=node("button",i+" · "+(concept??"không có"));b.type="button";if(i===step)b.setAttribute("aria-current","step");b.addEventListener("click",()=>stepTo(i));li.append(b);$("route").append(li);});}
function renderClosed(s){
 const c=s.comparison;$("ranking").replaceChildren();$("concept").textContent=s.served_item.concept+" · "+s.served_item.question+" · difficulty "+s.served_item.difficulty;
 $("baseline").textContent="Query timestamp đã ghi: "+s.timestamp+". Không gán timestamp thành argument của select.";
 $("comparison").textContent=c?(c.common_before?"So với graph-free: toàn bộ lịch sử trước bước này còn giống; current served tuple "+(c.current_same_served_tuple?"giữ":"khác")+". Không phải paired ΔP hoặc causal effect.":"Histories đã khác trước bước này: không so ΔP/loss như cùng target."):"Reference graph-free. Chọn full hoặc empty estimator để xem common-prefix comparison.";
 $("prefix-status").textContent=!c?"Chưa chọn comparison với graph-free.":(c.common_before?(c.common_after?"Common-before và common-after: lịch sử vẫn giống qua bước này.":"Common-before còn đúng; sau bước này histories bắt đầu diverge."):"Đã diverge: common-prefix flag giữ false, dù một số items về sau có thể trùng.");
 const jump=$("jump-break");jump.disabled=!c||c.first_break_step===null;jump.onclick=c&&c.first_break_step!==null?()=>stepTo(c.first_break_step):null;
 if(c&&c.negative_case)$("prefix-status").textContent+=" Không có tuple break trong 120 steps (negative case, không equivalence proof).";
 else if(c)$("prefix-status").textContent+=" First break: bước "+c.first_break_step+" · "+c.first_break_reasons.map(r=>({served_tuple:"served tuple",timestamp:"timestamp",label:"đáp án quan sát"}[r]||r)).join(", ")+".";
 const proof=c&&c.explanation;
 if(proof){
  $("ranking-caption").textContent=proof.classification==="SAME_B_TIES_NATIVE_B_SCORE_RANKING_EXPLAINS_CONCEPT_CHOICE"?"First common-prefix break: native B-score key tái hiện chosen concepts khác nhau khi membership và tie context giữ. Giải thích source-local CID, post-hoc; không giải thích qid/difficulty hoặc edge-only benefit.":"First common-prefix break có membership đổi; không gọi đây là score-only explanation. Chỉ hiển thị archived native keys.";
  for(const [variant,keys] of Object.entries(proof.ranking_keys))for(const r of keys)tableRow("ranking",[labels[variant]||variant,r.concept,r.score.toFixed(6),r.chapter_tie,r.prior_visits,r.selected?"✓":"—"]);
 }else{
  $("ranking-caption").textContent="Các native mastery_score calls thực sự được gọi trên B ở bước này. Complete tie keys chỉ archive ở first tuple break; không điền visits/chapter giả. Score không là calibrated probability.";
  for(const r of s.native_B_scores)tableRow("ranking",[labels[s.variant],r.concept,r.score.toFixed(6),"không archive","không archive",r.concept===s.served_item.concept?"✓":"—"]);
 }
}
async function loadSnapshot(){const request=++currentRequest;const closed=$("mode").value==="closed_loop";showMode(closed);const q=new URLSearchParams({profile:$("profile").value,seed:$("seed").value,variant:$("variant").value,step:$("step").value});const s=await get((closed?"/api/closed-loop?":"/api/replay?")+q);if(request!==currentRequest)return;
 $("step-label").textContent=s.step+" / 119";$("previous").disabled=s.step===0;$("next").disabled=s.step===119;
 if(closed){$("probability").textContent=s.p_correct_served_item.toFixed(6);renderClosed(s);}else{
  $("probability").textContent=s.p_correct_logged_query.toFixed(6);$("concept").textContent=s.concept_preview===null?"Không có concept preview":s.concept_preview;
  $("comparison").textContent="So với graph-free: scalar p "+(s.reference.p_changed_exact?"khác (so sánh exact)":"giữ nguyên")+"; concept preview "+(s.reference.preview_changed?"khác":"giữ nguyên")+".";
  $("baseline").textContent="Graph-free cùng snapshot: p = "+s.reference.p_correct_logged_query.toFixed(6)+"; preview = "+(s.reference.concept_preview??"không có")+".";
 }
 renderConcepts(s,closed);renderRoute(closed?s.route_served:s.route_preview,s.step);
}
async function init(){const c=await get("/api/catalog");option("mode",c.modes.map(m=>m.id),id=>c.modes.find(m=>m.id===id).label);option("profile",c.profiles);option("seed",c.seeds);option("variant",c.variants,v=>labels[v]||v);$("step").max=String(c.steps-1);$("step").disabled=false;$("coverage").textContent=c.profiles.length+" profile × "+c.seeds.length+" seed × "+c.variants.length+" variant × "+c.steps+" bước. Đổi lựa chọn không tạo simulation hoặc prediction mới.";
 const summary=c.closed_loop.reviewed_summary;$("closed-takeaway").textContent="POST-HOC / 9 seed-profile comparisons mỗi candidate: full có "+summary.full_same_membership_score_choices+" B-score/CID choices khi membership giữ và "+summary.full_membership_change+" membership change; empty có "+summary.empty_same_membership_score_choices+" score choices và "+summary.empty_negative_cases+" không tuple break. Không 9 independent seeds, new independent N = 0.";
 for(const id of ["mode","profile","seed","variant"])$(id).addEventListener("change",()=>loadSnapshot().catch(fail));$("step").addEventListener("input",()=>loadSnapshot().catch(fail));$("previous").addEventListener("click",()=>stepTo(Math.max(0,Number($("step").value)-1)));$("next").addEventListener("click",()=>stepTo(Math.min(c.steps-1,Number($("step").value)+1)));
 for(const r of c.rq1)tableRow("rq1",[labels[r.candidate],r.event_pairs,r.changed_probability_events,r.changed_mastery_events_any_concept,r.changed_ready_events,r.changed_action_preview_events]);
 const full=c.rq1.find(r=>r.candidate==="graph_package"),empty=c.rq1.find(r=>r.candidate==="empty_graph_package");const keep=full.conditional_tables.find(r=>r.first==="p_changed"&&r.second==="a_changed"&&r.first_changed&&!r.second_changed);
 $("rq1-takeaway").textContent="Graph package đầy đủ: "+keep.count+"/"+keep.conditional_denominator+" snapshot có P đổi nhưng concept preview giữ. Empty graph package: "+empty.changed_probability_events+" P đổi, "+empty.changed_mastery_events_any_concept+" mastery / "+empty.changed_ready_events+" ready / "+empty.changed_action_preview_events+" preview đổi. Package không đồng nghĩa riêng các cạnh.";
 for(const r of c.rq2_synthetic.profiles)tableRow("rq2",[r.profile,r.seed_blocks,r.mean_lambda_edge_interaction.toFixed(6),r.mechanism_exposed_events+" / "+r.mechanism_event_denominator]);
 const contrast=c.rq2_synthetic.paired_profile_contrasts.find(r=>r.contrast==="I(PYH)-I(PY)");if(contrast)$("rq2-takeaway").textContent="PYH − PY: mean "+contrast.mean.toFixed(6)+" Elo; "+contrast.signs.positive+" seed dương / "+contrast.signs.negative+" seed âm. Leave-one-seed-out mean ["+contrast.loo_min.toFixed(6)+", "+contrast.loo_max.toFixed(6)+"]. Thứ tự chưa ổn định; đây là sensitivity mô tả, không CI.";
 for(const m of c.models)$("models").append(node("dt",m.name),node("dd",m.status));for(const s of c.sources){const li=node("li");li.append(node("strong",s.run+" / "+s.file),node("div","Output SHA-256: "+s.sha256),node("div","Manifest SHA-256: "+s.manifest_sha256));$("sources").append(li);}for(const limit of [...c.limits_vi,...c.closed_loop.limits_vi])$("limits").append(node("li",limit));await loadSnapshot();
}
init().catch(fail);

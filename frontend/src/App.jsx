import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  ArrowRight, BookOpen, BrainCircuit, Check, ChevronRight, CircleHelp,
  FileText, GraduationCap, Library, Loader2, MessageSquareText, RefreshCw,
  Search, Sparkles, Target, Upload, X,
} from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const TABS = [
  ["lecture", "Lecture", BookOpen], ["guide", "Study guide", Sparkles],
  ["ask", "Ask Lumi", MessageSquareText], ["quiz", "Quiz", CircleHelp],
];
const PIPELINE = ["PARSING", "CHUNKING", "EMBEDDING", "GENERATING"];

export default function App() {
  const [document, setDocument] = useState(null);
  const [library, setLibrary] = useState([]);
  const [tab, setTab] = useState("lecture");
  const [data, setData] = useState({});
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { loadLibrary(); }, []);
  useEffect(() => {
    if (!document || ["COMPLETED", "FAILED"].includes(document.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const next = (await axios.get(`${API}/documents/${document.id}/status`)).data;
        setDocument(next);
        if (next.status === "COMPLETED") loadArtifact("lecture", next.id);
      } catch { /* retain the last known job state */ }
    }, 800);
    return () => window.clearInterval(timer);
  }, [document?.id, document?.status]);

  async function loadLibrary() {
    try { setLibrary((await axios.get(`${API}/documents`)).data); } catch { /* backend may be offline */ }
  }

  async function uploadFile(file) {
    if (!file) return;
    setUploading(true); setError(""); setData({});
    const form = new FormData(); form.append("file", file);
    try {
      const next = (await axios.post(`${API}/documents`, form)).data;
      setDocument(next); setTab("lecture");
      if (next.status === "COMPLETED") await loadArtifact("lecture", next.id);
      loadLibrary();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not upload this document.");
    } finally { setUploading(false); }
  }

  async function loadArtifact(nextTab, id = document?.id) {
    setTab(nextTab); setError("");
    if (!id || nextTab === "ask" || data[nextTab]) return;
    const path = nextTab === "guide" ? "study-guide" : nextTab;
    try {
      const response = await axios.get(`${API}/documents/${id}/${path}`);
      setData((current) => ({ ...current, [nextTab]: response.data }));
    } catch (requestError) { setError(requestError.response?.data?.detail || "Content could not be loaded."); }
  }

  function openDocument(item) {
    setDocument(item); setData({}); setTab("lecture"); setError("");
    if (item.status === "COMPLETED") loadArtifact("lecture", item.id);
  }

  if (!document) return <Home library={library} error={error} uploading={uploading} onUpload={uploadFile} onOpen={openDocument} />;
  const ready = document.status === "COMPLETED";
  return (
    <div className="min-h-screen bg-[#f5f3ee] text-[#18231d]">
      <header className="border-b border-[#dcd9cf] bg-[#fbfaf7]/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-5">
          <button className="flex items-center gap-2.5" onClick={() => setDocument(null)}>
            <Logo /><span className="font-display text-xl font-semibold">LumiNote</span>
          </button>
          <div className="flex items-center gap-3 text-sm text-[#647067]">
            <span className="hidden sm:inline">Grounded in your sources</span>
            <span className="flex items-center gap-1.5 rounded-full bg-[#e5f2e9] px-3 py-1.5 font-semibold text-[#246441]"><Check size={14} /> Private workspace</span>
          </div>
        </div>
      </header>

      {!ready ? <Processing document={document} onClose={() => setDocument(null)} /> : (
        <main className="mx-auto grid max-w-[1500px] lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="border-r border-[#dcd9cf] bg-[#efede6] px-4 py-6 lg:min-h-[calc(100vh-64px)]">
            <button onClick={() => setDocument(null)} className="mb-6 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-[#647067] hover:bg-white"><Library size={17} /> Library</button>
            <p className="px-3 text-[11px] font-bold uppercase tracking-[.16em] text-[#899087]">Learning space</p>
            <nav className="mt-2 space-y-1">
              {TABS.map(([key, label, Icon]) => <button key={key} onClick={() => loadArtifact(key)} className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${tab === key ? "bg-[#183f2a] text-white shadow-sm" : "text-[#536057] hover:bg-white"}`}><Icon size={18} />{label}</button>)}
            </nav>
            <div className="mt-8 rounded-2xl border border-[#d7d4c9] bg-[#fbfaf7] p-4">
              <p className="truncate font-semibold">{document.filename}</p>
              <div className="mt-3 flex gap-4 text-xs text-[#6f776f]"><span>{document.page_count} pages</span><span>{document.chunk_count} sources</span></div>
            </div>
          </aside>
          <section className="min-w-0 px-5 py-7 md:px-10 md:py-9">
            {error && <Alert message={error} onClose={() => setError("")} />}
            {tab === "lecture" && <Lecture data={data.lecture} onExplain={async (section, mode) => {
              const response = await axios.post(`${API}/documents/${document.id}/explain`, { section_id: section.id, mode });
              setData((current) => ({ ...current, explanation: { section: section.id, ...response.data } }));
            }} explanation={data.explanation} />}
            {tab === "guide" && <Guide data={data.guide} />}
            {tab === "ask" && <Ask documentId={document.id} />}
            {tab === "quiz" && <Quiz data={data.quiz} />}
          </section>
        </main>
      )}
    </div>
  );
}

function Home({ library, error, uploading, onUpload, onOpen }) {
  const [dragging, setDragging] = useState(false);
  return <div className="min-h-screen bg-[#f5f3ee] text-[#18231d]">
    <header className="mx-auto flex h-20 max-w-7xl items-center justify-between px-6"><div className="flex items-center gap-2.5"><Logo /><span className="font-display text-xl font-semibold">LumiNote</span></div><span className="rounded-full border border-[#dad7cd] bg-white/60 px-4 py-2 text-sm font-medium text-[#59645c]">AI learning studio</span></header>
    <main className="mx-auto grid max-w-7xl items-center gap-14 px-6 pb-20 pt-10 lg:grid-cols-[1.05fr_.95fr] lg:pt-20">
      <section>
        <span className="inline-flex items-center gap-2 rounded-full bg-[#e2eee5] px-3 py-1.5 text-xs font-bold uppercase tracking-[.13em] text-[#2c6846]"><Sparkles size={14} /> Learn from what you trust</span>
        <h1 className="font-display mt-6 max-w-3xl text-5xl font-medium leading-[1.02] tracking-[-.045em] sm:text-7xl">Turn dense PDFs into <em className="font-normal text-[#be5b3f]">clear understanding.</em></h1>
        <p className="mt-7 max-w-xl text-lg leading-8 text-[#667168]">Upload your notes, papers, or textbooks. LumiNote builds a cited lecture, study guide, and quiz—and answers questions using only your document.</p>
        <div className="mt-9 grid max-w-xl grid-cols-3 gap-3">
          {[[BrainCircuit,"Cited answers"],[Target,"Active recall"],[GraduationCap,"Guided learning"]].map(([Icon,label]) => <div className="rounded-2xl border border-[#dedbd1] bg-[#fbfaf7] p-4 text-sm font-semibold" key={label}><Icon className="mb-3 text-[#367651]" size={21}/>{label}</div>)}
        </div>
      </section>
      <section>
        <label onDragOver={(e) => {e.preventDefault();setDragging(true)}} onDragLeave={() => setDragging(false)} onDrop={(e) => {e.preventDefault();setDragging(false);onUpload(e.dataTransfer.files?.[0])}} className={`group block cursor-pointer rounded-[28px] border-2 border-dashed p-3 transition ${dragging ? "border-[#34714e] bg-[#e8f2ea]" : "border-[#cfcbbf] bg-[#ebe8df] hover:border-[#7e9b87]"}`}>
          <div className="rounded-[21px] bg-[#fbfaf7] px-8 py-14 text-center shadow-[0_18px_70px_rgba(47,55,48,.08)]">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[#183f2a] text-white shadow-lg shadow-[#183f2a]/20">{uploading ? <Loader2 className="animate-spin" /> : <Upload />}</div>
            <h2 className="font-display mt-6 text-2xl font-semibold">Drop your PDF here</h2><p className="mt-2 text-sm text-[#737b74]">or click to browse · up to 25 MB</p>
            <div className="mx-auto mt-7 flex w-fit items-center gap-2 rounded-full bg-[#f0eee8] px-4 py-2 text-xs font-semibold text-[#657068]"><FileText size={14}/> Text and scanned PDFs supported</div>
            <input className="sr-only" type="file" accept="application/pdf,.pdf" onChange={(e) => onUpload(e.target.files?.[0])}/>
          </div>
        </label>
        {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </section>
    </main>
    {library.length > 0 && <section className="mx-auto max-w-7xl px-6 pb-20"><div className="mb-4 flex items-end justify-between"><div><p className="text-xs font-bold uppercase tracking-[.16em] text-[#7d857d]">Your library</p><h2 className="font-display mt-1 text-2xl font-semibold">Continue learning</h2></div></div><div className="grid gap-3 md:grid-cols-3">{library.slice(0,3).map(item => <button key={item.id} onClick={() => onOpen(item)} className="group rounded-2xl border border-[#ddd9cf] bg-[#fbfaf7] p-5 text-left transition hover:-translate-y-0.5 hover:shadow-lg"><FileText className="text-[#34714e]"/><p className="mt-5 truncate font-semibold">{item.filename}</p><p className="mt-1 text-xs text-[#7b837c]">{item.page_count || "—"} pages · {item.status.toLowerCase()}</p><ArrowRight className="ml-auto mt-4 text-[#9aa099] transition group-hover:translate-x-1" size={18}/></button>)}</div></section>}
  </div>;
}

function Processing({ document, onClose }) {
  const active = Math.max(0, PIPELINE.indexOf(document.status));
  return <main className="mx-auto flex min-h-[calc(100vh-64px)] max-w-3xl items-center px-6"><div className="w-full rounded-[28px] border border-[#ddd9cf] bg-[#fbfaf7] p-8 shadow-xl shadow-black/5 md:p-12"><div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-[.15em] text-[#34714e]">Building your learning space</p><h1 className="font-display mt-3 truncate text-3xl font-semibold">{document.filename}</h1></div><button onClick={onClose}><X size={20}/></button></div><div className="mt-8 h-2 overflow-hidden rounded-full bg-[#e3e0d7]"><div style={{width:`${document.progress}%`}} className="h-full rounded-full bg-[#be5b3f] transition-all duration-500"/></div><p className="mt-2 text-right text-xs font-semibold text-[#737b74]">{document.progress}%</p><div className="mt-8 grid gap-3 sm:grid-cols-4">{PIPELINE.map((step,index)=><div key={step} className={`rounded-2xl border p-4 ${index <= active ? "border-[#a9c4b1] bg-[#e7f0e9]" : "border-[#e1ded5]"}`}><div className="mb-4">{index < active || document.status === "COMPLETED" ? <Check size={18}/> : index === active ? <Loader2 className="animate-spin" size={18}/> : <span className="block h-4 w-4 rounded-full border"/>}</div><p className="text-xs font-bold">{step.charAt(0)+step.slice(1).toLowerCase()}</p></div>)}</div>{document.status === "FAILED" && <p className="mt-6 rounded-xl bg-red-50 p-4 text-red-700">{document.error}</p>}</div></main>;
}

function Lecture({ data, onExplain, explanation }) {
  const [selected, setSelected] = useState(0);
  if (!data) return <Loading />;
  const section = data.sections[selected];
  return <div className="mx-auto max-w-5xl"><Eyebrow>Structured lecture</Eyebrow><h1 className="font-display mt-2 text-4xl font-semibold tracking-tight">{data.title}</h1><div className="mt-8 grid gap-6 xl:grid-cols-[220px_1fr]"><nav className="space-y-1">{data.sections.map((item,index)=><button key={item.id} onClick={()=>setSelected(index)} className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm font-semibold ${selected===index?"bg-[#e1eee4] text-[#245d3d]":"text-[#6c756e] hover:bg-white"}`}><span className="truncate">{String(index+1).padStart(2,"0")} · {item.title}</span><ChevronRight size={15}/></button>)}</nav><article className="rounded-[24px] border border-[#ddd9cf] bg-[#fbfaf7] p-6 shadow-sm md:p-9"><span className="text-xs font-bold uppercase tracking-[.14em] text-[#b05238]">Section {selected+1}</span><h2 className="font-display mt-3 text-3xl font-semibold">{section.title}</h2><p className="mt-5 text-[17px] leading-8 text-[#4e5b52]">{section.explanation}</p><div className="mt-7 space-y-3">{section.key_points.map((point,index)=><div key={point} className="flex gap-3 rounded-xl bg-[#f0eee8] p-4"><span className="font-display text-[#b05238]">{index+1}</span><p className="leading-6">{point}</p></div>)}</div><div className="mt-7 flex flex-wrap gap-2">{["simpler","example","analogy","deeper"].map(mode=><button key={mode} onClick={()=>onExplain(section,mode)} className="rounded-full border border-[#d2cec3] bg-white px-4 py-2 text-xs font-bold capitalize hover:border-[#34714e]">{mode}</button>)}</div>{explanation?.section===section.id && <div className="mt-5 rounded-2xl border border-[#b9d0c0] bg-[#e8f2ea] p-5"><p className="text-xs font-bold uppercase tracking-wider text-[#34714e]">Lumi explains</p><p className="mt-2 leading-7">{explanation.explanation}</p></div>}<Citations items={section.citations}/></article></div></div>;
}

function Guide({ data }) { if(!data) return <Loading/>; return <div className="mx-auto max-w-5xl"><Eyebrow>Study guide</Eyebrow><h1 className="font-display mt-2 text-4xl font-semibold">The essentials, organized.</h1><div className="mt-8 grid gap-4 md:grid-cols-2">{[["Major concepts",data.major_concepts,BrainCircuit],["Definitions",data.definitions,BookOpen],["Important facts",data.important_facts,Target],["Common mistakes",data.common_mistakes,RefreshCw]].map(([title,items,Icon])=><section key={title} className="rounded-[22px] border border-[#ddd9cf] bg-[#fbfaf7] p-6"><Icon className="text-[#34714e]"/><h2 className="font-display mt-4 text-2xl font-semibold">{title}</h2><ul className="mt-4 space-y-3">{items.map(item=><li key={item} className="flex gap-3 text-sm leading-6 text-[#57635a]"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#be5b3f]"/>{item}</li>)}</ul></section>)}</div></div> }

function Ask({ documentId }) { const [question,setQuestion]=useState(""); const [messages,setMessages]=useState([]); const [loading,setLoading]=useState(false); async function ask(e){e.preventDefault();if(question.trim().length<3)return;const prompt=question;setQuestion("");setMessages(m=>[...m,{role:"user",text:prompt}]);setLoading(true);try{const result=(await axios.post(`${API}/documents/${documentId}/ask`,{question:prompt})).data;setMessages(m=>[...m,{role:"assistant",text:result.answer,citations:result.citations}]);}catch{setMessages(m=>[...m,{role:"assistant",text:"I couldn't retrieve an answer right now."}]);}finally{setLoading(false)}} return <div className="mx-auto flex min-h-[calc(100vh-135px)] max-w-4xl flex-col"><Eyebrow>Ask the document</Eyebrow><h1 className="font-display mt-2 text-4xl font-semibold">What would you like to understand?</h1><div className="mt-7 flex-1 space-y-4">{messages.length===0&&<div className="rounded-[24px] border border-[#ddd9cf] bg-[#fbfaf7] p-8 text-center"><Search className="mx-auto text-[#34714e]"/><p className="mt-4 font-semibold">Answers are retrieved from your PDF</p><p className="mt-1 text-sm text-[#778078]">Every supported answer includes page-level sources.</p></div>}{messages.map((m,i)=><div key={i} className={`max-w-[85%] rounded-2xl p-5 ${m.role==="user"?"ml-auto bg-[#183f2a] text-white":"border border-[#ddd9cf] bg-[#fbfaf7]"}`}><p className="leading-7">{m.text}</p>{m.citations&&<Citations items={m.citations}/>}</div>)}{loading&&<Loader2 className="animate-spin text-[#34714e]"/>}</div><form onSubmit={ask} className="sticky bottom-5 mt-6 flex gap-2 rounded-2xl border border-[#cecabe] bg-white p-2 shadow-xl"><input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Ask a question about this PDF…" className="min-w-0 flex-1 bg-transparent px-3 outline-none"/><button className="rounded-xl bg-[#be5b3f] px-5 py-3 font-semibold text-white">Ask</button></form></div> }

function Quiz({ data }) { const [answers,setAnswers]=useState({}); if(!data)return <Loading/>; const complete=Object.keys(answers).length===data.questions.length; const score=Object.entries(answers).filter(([id,value])=>data.questions.find(q=>q.id===id)?.correct_index===value).length; return <div className="mx-auto max-w-4xl"><Eyebrow>Active recall</Eyebrow><div className="flex items-end justify-between"><h1 className="font-display mt-2 text-4xl font-semibold">Check your understanding.</h1>{complete&&<span className="rounded-full bg-[#e1eee4] px-4 py-2 font-bold text-[#246441]">{score}/{data.questions.length} correct</span>}</div><div className="mt-8 space-y-5">{data.questions.map((q,index)=><section key={q.id} className="rounded-[22px] border border-[#ddd9cf] bg-[#fbfaf7] p-6"><p className="text-xs font-bold uppercase tracking-wider text-[#9a5a46]">{q.difficulty} · Question {index+1}</p><h2 className="mt-3 text-lg font-semibold leading-7">{q.question}</h2><div className="mt-5 grid gap-2">{q.options.map((option,i)=><button key={`${q.id}-${i}`} onClick={()=>setAnswers(a=>({...a,[q.id]:i}))} className={`rounded-xl border p-3 text-left text-sm ${answers[q.id]===i?"border-[#34714e] bg-[#e7f0e9]":"border-[#dedbd1] hover:bg-[#f2f0ea]"}`}>{String.fromCharCode(65+i)}. {option}</button>)}</div>{answers[q.id]!==undefined&&<p className="mt-4 border-t border-[#e3e0d8] pt-4 text-sm leading-6 text-[#5d675f]"><strong>{answers[q.id]===q.correct_index?"Correct. ":"Not quite. "}</strong>{q.explanation}</p>}</section>)}</div></div> }

function Citations({ items=[] }) { return items.length>0&&<div className="mt-6 border-t border-[#e2dfd6] pt-4"><p className="text-[10px] font-bold uppercase tracking-[.15em] text-[#899088]">Sources</p><div className="mt-2 flex flex-wrap gap-2">{items.map((item,i)=><span title={item.excerpt} key={`${item.chunk_index}-${i}`} className="rounded-full bg-[#e7eee8] px-3 py-1.5 text-xs font-bold text-[#306647]">Page {item.page}</span>)}</div></div> }
function Loading(){return <div className="flex min-h-[50vh] items-center justify-center"><Loader2 className="animate-spin text-[#34714e]"/></div>}
function Alert({message,onClose}){return <div className="mb-5 flex justify-between rounded-xl bg-red-50 p-4 text-sm text-red-700"><span>{message}</span><button onClick={onClose}><X size={16}/></button></div>}
function Eyebrow({children}){return <p className="text-xs font-bold uppercase tracking-[.16em] text-[#b05238]">{children}</p>}
function Logo(){return <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#183f2a] text-[#f7e8c7]"><BookOpen size={18}/></span>}

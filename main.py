"""
╔══════════════════════════════════════════════════════════════════════════╗
║  AI-Driven Multi-Criteria Task Scheduling & Optimization System v2.0   ║
║  Developer : Rutuja | 3rd Year AIML                                     ║
║  Stack     : Python 3 + Tkinter  (zero extra libraries needed)          ║
║  Algorithms: Heuristic Scoring · Greedy Optimization · CSP              ║
║                                                                          ║
║  ALL 10 FEATURES:                                                        ║
║  ✅ 1. Search & Filter bar        ✅ 2. Priority progress bars           ║
║  ✅ 3. Deadline countdown         ✅ 4. Dark / Light theme toggle        ║
║  ✅ 5. Toast slide-in alerts      ✅ 6. Canvas bar chart                 ║
║  ✅ 7. Overload warning banner    ✅ 8. Edit task dialog                 ║
║  ✅ 9. Export to CSV              ✅ 10. Confetti on task done           ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import json, os, math, csv, random

# ─────────────────────────────────────────────────────────────────────────────
#  THEMES
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "BG_DARK": "#0f0f1a", "BG_CARD": "#1a1a2e", "BG_INPUT": "#16213e",
        "ACCENT": "#7c3aed", "ACCENT2": "#06b6d4", "SUCCESS": "#10b981",
        "WARNING": "#f59e0b", "DANGER": "#ef4444", "TEXT_PRIMARY": "#f1f5f9",
        "TEXT_MUTED": "#94a3b8", "BORDER": "#2d2d4e", "LOG_BG": "#0d0d1f",
    },
    "light": {
        "BG_DARK": "#eef2ff", "BG_CARD": "#ffffff", "BG_INPUT": "#e8edf7",
        "ACCENT": "#6d28d9", "ACCENT2": "#0891b2", "SUCCESS": "#059669",
        "WARNING": "#d97706", "DANGER": "#dc2626", "TEXT_PRIMARY": "#1e293b",
        "TEXT_MUTED": "#475569", "BORDER": "#cbd5e1", "LOG_BG": "#f1f5f9",
    }
}
T = dict(THEMES["dark"])

FONT_TITLE   = ("Segoe UI", 17, "bold")
FONT_HEADING = ("Segoe UI", 12, "bold")
FONT_BODY    = ("Segoe UI", 10)
FONT_SMALL   = ("Segoe UI", 9)
FONT_MONO    = ("Consolas", 9)


# ─────────────────────────────────────────────────────────────────────────────
#  AI ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class AIEngine:
    """
    ALGORITHM 1 – Heuristic Multi-Criteria Scoring
       P = 0.4·Importance + 0.3·Urgency + 0.2·Difficulty − 0.1·Time
    ALGORITHM 2 – Greedy Optimization   (sort by score desc)
    ALGORITHM 3 – Constraint Satisfaction Problem (CSP flags)
    """
    WEIGHTS = {"importance": 0.40, "urgency": 0.30,
               "difficulty": 0.20, "time":    0.10}
    DAILY_HOUR_CAP = 10

    @staticmethod
    def days_remaining(dl_str):
        try:
            return float((datetime.strptime(dl_str, "%Y-%m-%d").date()
                          - date.today()).days)
        except ValueError:
            return 0.0

    @staticmethod
    def normalize(v, lo, hi):
        return 0.5 if hi == lo else (v - lo) / (hi - lo)

    @staticmethod
    def urgency(days):
        return 1.0 if days <= 0 else min(math.exp(-days / 7.0), 1.0)

    @classmethod
    def score(cls, task, np):
        w = cls.WEIGHTS
        return round(
            w["importance"] * cls.normalize(task["importance"], 1, 5)
          + w["urgency"]    * cls.urgency(task["days_remaining"])
          + w["difficulty"] * cls.normalize(task["difficulty"], 1, 5)
          - w["time"]       * cls.normalize(task["estimated_hours"],
                                            np["min_t"], np["max_t"]), 4)

    @classmethod
    def constrain(cls, t):
        d, h = t["days_remaining"], t["estimated_hours"]
        if   d < 0:              t.update(constraint_flag="OVERDUE",  feasible=False)
        elif d <= 2:             t.update(constraint_flag="CRITICAL", feasible=True)
        elif h > cls.DAILY_HOUR_CAP: t.update(constraint_flag="OVERLOAD", feasible=True)
        else:                    t.update(constraint_flag="OK",       feasible=True)
        return t

    @classmethod
    def run(cls, raw):
        if not raw: return []
        for t in raw:
            t["days_remaining"] = cls.days_remaining(t["deadline"])
        hrs = [t["estimated_hours"] for t in raw]
        np  = {"min_t": min(hrs), "max_t": max(hrs)}
        for t in raw:
            t["priority_score"] = cls.score(t, np)
            cls.constrain(t)
        ranked = sorted(raw, key=lambda x: x["priority_score"], reverse=True)
        for i, t in enumerate(ranked):
            t["rank"] = i + 1
        return ranked


# ─────────────────────────────────────────────────────────────────────────────
#  PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA  = os.path.join(_HERE, "tasks_data.json")
_KEYS = ["id","name","deadline","importance","difficulty",
         "estimated_hours","category","status"]

def load():
    return json.load(open(DATA)) if os.path.exists(DATA) else []

def save(tasks):
    json.dump([{k:t[k] for k in _KEYS if k in t} for t in tasks],
              open(DATA,"w"), indent=2)


# ─────────────────────────────────────────────────────────────────────────────
#  FEATURE 5 — TOAST NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────
class Toast:
    _ICONS = {"success":"✅","warning":"⚠️","danger":"🔴","info":"ℹ️"}
    _COLS  = {"success": "SUCCESS","warning":"WARNING",
              "danger":"DANGER","info":"ACCENT2"}

    def __init__(self, root):
        self.root=root; self._q=[]; self._busy=False

    def show(self, msg, kind="success"):
        self._q.append((msg, kind))
        if not self._busy: self._next()

    def _next(self):
        if not self._q: self._busy=False; return
        self._busy=True
        msg, kind = self._q.pop(0)
        color = T[self._COLS.get(kind,"ACCENT2")]
        w = tk.Toplevel(self.root)
        w.overrideredirect(True); w.attributes("-topmost",True)
        w.configure(bg=color)
        tk.Label(w, text=f"  {self._ICONS.get(kind,'ℹ️')}  {msg}  ",
                 bg=color, fg="white",
                 font=("Segoe UI",10,"bold"), padx=10, pady=8).pack()
        self.root.update_idletasks()
        rx = self.root.winfo_x() + self.root.winfo_width() - 330
        ry = self.root.winfo_y() + 68
        w.geometry(f"310x36+{rx}+{ry-40}")
        self._slide(w, ry, ry-40)

    def _slide(self, w, ty, cy):
        if not w.winfo_exists(): self._next(); return
        cy += 4
        if cy < ty:
            w.geometry(f"310x36+{w.winfo_x()}+{cy}")
            self.root.after(8, lambda: self._slide(w, ty, cy))
        else:
            self.root.after(1800, lambda: self._fade(w, 1.0))

    def _fade(self, w, a):
        if not w.winfo_exists(): self._next(); return
        if a > 0:
            try: w.attributes("-alpha", a); self.root.after(28, lambda: self._fade(w, a-0.07))
            except: pass
        else:
            try: w.destroy()
            except: pass
            self._next()


# ─────────────────────────────────────────────────────────────────────────────
#  FEATURE 10 — CONFETTI
# ─────────────────────────────────────────────────────────────────────────────
class Confetti:
    _COLS = ["#ff6b6b","#ffd93d","#6bcb77","#4d96ff","#c77dff",
             "#ff9f43","#00d2d3","#ff6348","#a29bfe","#fd79a8"]

    def __init__(self, root):
        self.root=root; self._on=False; self._cv=None; self._ps=[]

    def burst(self):
        if self._on: return
        self._on=True
        self._cv = tk.Canvas(self.root, highlightthickness=0,
                              bg=T["BG_DARK"], bd=0)
        self._cv.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.root.update_idletasks()
        W=self.root.winfo_width(); H=self.root.winfo_height()
        self._ps=[]
        for _ in range(70):
            x=random.randint(0,W); y=random.randint(-H//2,0)
            dx=random.uniform(-2.5,2.5); dy=random.uniform(3.5,7.5)
            s=random.randint(6,14); col=random.choice(self._COLS)
            fn = self._cv.create_rectangle if random.random()<.5 else self._cv.create_oval
            obj = fn(x,y,x+s,y+s,fill=col,outline="")
            self._ps.append([obj,dx,dy,H])
        self._anim(0)

    def _anim(self, f):
        if not self._on or not self._cv: return
        all_done=True
        for p in self._ps:
            obj,dx,dy,mh=p
            self._cv.move(obj,dx,dy)
            if self._cv.coords(obj) and self._cv.coords(obj)[1]<mh+20:
                all_done=False
        if f<90 and not all_done: self.root.after(16,lambda:self._anim(f+1))
        else: self._stop()

    def _stop(self):
        self._on=False
        if self._cv:
            try: self._cv.destroy()
            except: pass
            self._cv=None


# ─────────────────────────────────────────────────────────────────────────────
#  FEATURE 8 — EDIT DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class EditDialog(tk.Toplevel):
    def __init__(self, parent, task, cb):
        super().__init__(parent)
        self.task=task; self.cb=cb
        self.title("✏️  Edit Task"); self.geometry("430x500")
        self.resizable(False,False); self.configure(bg=T["BG_CARD"])
        self.grab_set(); self._build()

    def _build(self):
        tk.Label(self, text="✏️  Edit Task", bg=T["BG_CARD"],
                 fg=T["ACCENT2"], font=FONT_HEADING
                 ).pack(anchor="w", padx=20, pady=(16,4))
        tk.Frame(self, bg=T["BORDER"], height=1).pack(fill="x", padx=20)

        fm = tk.Frame(self, bg=T["BG_CARD"]); fm.pack(fill="x", padx=20, pady=8)

        def lbl(t):
            tk.Label(fm, text=t, bg=T["BG_CARD"], fg=T["TEXT_MUTED"],
                     font=FONT_SMALL, anchor="w").pack(fill="x", pady=(7,1))
        def ent(val):
            e = tk.Entry(fm, bg=T["BG_INPUT"], fg=T["TEXT_PRIMARY"],
                         insertbackground=T["ACCENT2"], relief="flat",
                         font=FONT_BODY, bd=0, highlightthickness=1,
                         highlightbackground=T["BORDER"], highlightcolor=T["ACCENT2"])
            e.pack(fill="x", ipady=5); e.insert(0, str(val)); return e
        def sld(label, var, lo, hi, col):
            lbl(label)
            sf=tk.Frame(fm,bg=T["BG_CARD"]); sf.pack(fill="x")
            ttk.Scale(sf,from_=lo,to=hi,variable=var,orient="horizontal"
                      ).pack(side="left",fill="x",expand=True)
            vl=tk.Label(sf,bg=T["BG_CARD"],fg=col,font=("Segoe UI",10,"bold"),width=4)
            vl.pack(side="left",padx=4)
            def u(*_): vl.config(text=str(int(var.get())) if lo==1 and hi==5
                                  else f"{var.get():.1f}h")
            var.trace_add("write",u); u()

        lbl("Task Name");         self.en = ent(self.task["name"])
        lbl("Deadline (YYYY-MM-DD)"); self.ed = ent(self.task["deadline"])
        self.vi=tk.IntVar(value=self.task["importance"])
        self.vd=tk.IntVar(value=self.task["difficulty"])
        self.vh=tk.DoubleVar(value=self.task["estimated_hours"])
        sld("Importance (1–5)", self.vi, 1, 5, T["ACCENT"])
        sld("Difficulty  (1–5)", self.vd, 1, 5, T["ACCENT2"])
        sld("Estimated Hours",  self.vh, 0.5, 12, T["WARNING"])

        tk.Frame(self,bg=T["BORDER"],height=1).pack(fill="x",padx=20,pady=10)
        bf=tk.Frame(self,bg=T["BG_CARD"]); bf.pack(fill="x",padx=20,pady=(0,16))

        def save():
            nm=self.en.get().strip(); dl=self.ed.get().strip()
            if not nm: messagebox.showerror("Error","Name empty!",parent=self); return
            try: datetime.strptime(dl,"%Y-%m-%d")
            except: messagebox.showerror("Error","Use YYYY-MM-DD!",parent=self); return
            self.task.update(name=nm, deadline=dl,
                             importance=int(self.vi.get()),
                             difficulty=int(self.vd.get()),
                             estimated_hours=round(float(self.vh.get()),1))
            self.cb(self.task); self.destroy()

        tk.Button(bf, text="💾  Save Changes", bg=T["ACCENT"], fg="white",
                  font=("Segoe UI",10,"bold"), relief="flat",
                  pady=9, cursor="hand2", command=save).pack(fill="x", pady=(0,6))
        tk.Button(bf, text="Cancel", bg=T["BG_INPUT"], fg=T["TEXT_MUTED"],
                  font=FONT_SMALL, relief="flat", pady=6,
                  cursor="hand2", command=self.destroy).pack(fill="x")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("AI-Driven Multi-Criteria Task Scheduling & Optimization System  v2.0")
        self.geometry("1280x800"); self.minsize(1080,700)
        self.configure(bg=T["BG_DARK"]); self.resizable(True,True)

        self.raw       = load()
        self._ctr      = max((t.get("id",0) for t in self.raw), default=0)+1
        self.opt       = []
        self._theme    = "dark"
        self._pi       = 0
        self._pc       = [T["ACCENT"],"#9d4edd","#c77dff",T["ACCENT2"],"#38bdf8"]

        self.toast     = Toast(self)
        self.confetti  = Confetti(self)

        self._ui(); self._ai(); self._pulse()

    # ── BUILD UI ──────────────────────────────────────────────────────────────
    def _ui(self):
        # Header
        self.hdr = tk.Frame(self, bg=T["BG_CARD"], height=62)
        self.hdr.pack(fill="x"); self.hdr.pack_propagate(False)

        self.ttl = tk.Label(self.hdr,
            text="🧠  AI-Driven Multi-Criteria Task Scheduling & Optimization System",
            bg=T["BG_CARD"], fg=T["ACCENT"], font=FONT_TITLE, anchor="w")
        self.ttl.pack(side="left", padx=18, pady=12)

        # Theme toggle (Feature 4)
        self.tbtn = tk.Button(self.hdr, text="☀️  Light Mode",
            bg=T["BG_INPUT"], fg=T["TEXT_MUTED"],
            relief="flat", font=FONT_SMALL, padx=10, pady=4,
            cursor="hand2", command=self._toggle_theme)
        self.tbtn.pack(side="right", padx=8, pady=16)

        tk.Label(self.hdr, text="⚡ Heuristic + Greedy + CSP",
                 bg=T["ACCENT"], fg="white", font=FONT_SMALL,
                 padx=10, pady=4).pack(side="right", padx=4, pady=16)

        self.clk = tk.Label(self.hdr, bg=T["BG_CARD"],
                             fg=T["TEXT_MUTED"], font=FONT_SMALL)
        self.clk.pack(side="right", padx=14)
        self._tick()

        # Overload banner (Feature 7) — hidden initially
        self.banner_frame = tk.Frame(self, bg=T["DANGER"], height=32)
        tk.Label(self.banner_frame,
                 text="⚠️  WORKLOAD OVERLOAD — Pending hours exceed 3× daily cap! Please reschedule some tasks.",
                 bg=T["DANGER"], fg="white",
                 font=("Segoe UI",9,"bold")).pack(pady=6)

        # Body
        body = tk.Frame(self, bg=T["BG_DARK"])
        body.pack(fill="both", expand=True, padx=10, pady=8)

        L = tk.Frame(body, bg=T["BG_DARK"], width=370)
        L.pack(side="left", fill="y", padx=(0,8)); L.pack_propagate(False)
        R = tk.Frame(body, bg=T["BG_DARK"])
        R.pack(side="left", fill="both", expand=True)

        self._form(L); self._results(R)

    # ── INPUT FORM ────────────────────────────────────────────────────────────
    def _form(self, p):
        card = tk.Frame(p, bg=T["BG_CARD"]); card.pack(fill="both", expand=True)

        tk.Label(card, text="➕  Add New Task", bg=T["BG_CARD"],
                 fg=T["ACCENT2"], font=FONT_HEADING
                 ).pack(anchor="w", padx=14, pady=(14,4))
        tk.Frame(card, bg=T["BORDER"], height=1).pack(fill="x", padx=14)

        fm = tk.Frame(card, bg=T["BG_CARD"]); fm.pack(fill="x", padx=14, pady=4)

        def lbl(t):
            tk.Label(fm, text=t, bg=T["BG_CARD"], fg=T["TEXT_MUTED"],
                     font=FONT_SMALL, anchor="w").pack(fill="x", pady=(7,1))
        def inp():
            e = tk.Entry(fm, bg=T["BG_INPUT"], fg=T["TEXT_PRIMARY"],
                         insertbackground=T["ACCENT2"], relief="flat",
                         font=FONT_BODY, bd=0, highlightthickness=1,
                         highlightbackground=T["BORDER"],
                         highlightcolor=T["ACCENT2"])
            e.pack(fill="x", ipady=5); return e
        def srow(label, var, lo, hi, col):
            lbl(label)
            sf=tk.Frame(fm,bg=T["BG_CARD"]); sf.pack(fill="x")
            ttk.Scale(sf,from_=lo,to=hi,variable=var,
                      orient="horizontal").pack(side="left",fill="x",expand=True)
            vl=tk.Label(sf,bg=T["BG_CARD"],fg=col,
                        font=("Segoe UI",10,"bold"),width=4)
            vl.pack(side="left",padx=4)
            def u(*_): vl.config(text=str(int(var.get())))
            var.trace_add("write",u); u()

        lbl("Task Name *");             self.en = inp()
        lbl("Deadline (YYYY-MM-DD) *"); self.ed = inp()
        self.ed.insert(0, str(date.today()))

        lbl("Category")
        cf=tk.Frame(fm,bg=T["BG_CARD"]); cf.pack(fill="x")
        self.vcat=tk.StringVar(value="Study"); self._cb={}
        for cat,ic in [("Study","📚"),("Work","💼"),("Personal","🏠")]:
            b=tk.Button(cf, text=f"{ic} {cat}",
                        bg=T["BG_INPUT"], fg=T["TEXT_MUTED"],
                        relief="flat", font=FONT_SMALL,
                        padx=8, pady=5, cursor="hand2",
                        command=lambda c=cat: self._cat(c))
            b.pack(side="left", padx=(0,5), pady=2); self._cb[cat]=b
        self._cat("Study")

        self.vi=tk.IntVar(value=3); self.vd=tk.IntVar(value=3)
        self.vh=tk.DoubleVar(value=2.0)
        srow("Importance (1=Low → 5=High)",  self.vi, 1, 5, T["ACCENT"])
        srow("Difficulty  (1=Easy → 5=Hard)", self.vd, 1, 5, T["ACCENT2"])

        lbl("Estimated Hours")
        hf=tk.Frame(fm,bg=T["BG_CARD"]); hf.pack(fill="x")
        ttk.Scale(hf,from_=0.5,to=12,variable=self.vh,
                  orient="horizontal").pack(side="left",fill="x",expand=True)
        hl=tk.Label(hf,bg=T["BG_CARD"],fg=T["WARNING"],
                    font=("Segoe UI",10,"bold"),width=5)
        hl.pack(side="left",padx=4)
        def uh(*_): hl.config(text=f"{self.vh.get():.1f}h")
        self.vh.trace_add("write",uh); uh()

        tk.Frame(card,bg=T["BORDER"],height=1).pack(fill="x",padx=14,pady=10)
        bf=tk.Frame(card,bg=T["BG_CARD"]); bf.pack(fill="x",padx=14,pady=(0,10))
        self._btn(bf,"✅  Add Task & Optimize",T["ACCENT"],"white",
                  self._add).pack(fill="x",pady=(0,6))
        self._btn(bf,"🗑  Clear All Tasks","#2d2d4e",T["TEXT_MUTED"],
                  self._clr).pack(fill="x")

        tk.Frame(card,bg=T["BORDER"],height=1).pack(fill="x",padx=14,pady=(4,0))
        fb=tk.Frame(card,bg=T["LOG_BG"]); fb.pack(fill="x",padx=14,pady=(0,14))
        tk.Label(fb,bg=T["LOG_BG"],fg=T["TEXT_MUTED"],font=FONT_SMALL,
                 text="⚙️  AI Formula:",anchor="w").pack(fill="x",padx=8,pady=(6,0))
        tk.Label(fb,bg=T["LOG_BG"],fg=T["ACCENT2"],font=FONT_MONO,
                 text="P = 0.4·Imp + 0.3·Urgency + 0.2·Diff − 0.1·Time",
                 anchor="w",wraplength=318).pack(fill="x",padx=8,pady=(2,8))

    def _btn(self, p, t, bg, fg, cmd):
        b=tk.Button(p,text=t,bg=bg,fg=fg,
                    font=("Segoe UI",10,"bold"),relief="flat",
                    pady=8,cursor="hand2",command=cmd)
        b.bind("<Enter>",lambda e:b.config(bg=self._lt(bg)))
        b.bind("<Leave>",lambda e:b.config(bg=bg))
        return b

    @staticmethod
    def _lt(h):
        try:
            r,g,b=int(h[1:3],16),int(h[3:5],16),int(h[5:7],16)
            return f"#{min(r+35,255):02x}{min(g+35,255):02x}{min(b+35,255):02x}"
        except: return h

    def _cat(self, c):
        self.vcat.set(c)
        for k,b in self._cb.items():
            b.config(bg=T["ACCENT"] if k==c else T["BG_INPUT"],
                     fg="white"     if k==c else T["TEXT_MUTED"])

    # ── RESULTS ───────────────────────────────────────────────────────────────
    def _results(self, p):
        self.sf=tk.Frame(p,bg=T["BG_DARK"])
        self.sf.pack(fill="x",pady=(0,8))
        self._cards()

        # Feature 1 — Search & Filter
        bar=tk.Frame(p,bg=T["BG_DARK"]); bar.pack(fill="x",pady=(0,6))
        tk.Label(bar,text="🔍",bg=T["BG_DARK"],
                 fg=T["TEXT_MUTED"],font=FONT_BODY).pack(side="left",padx=(0,4))
        self.sv=tk.StringVar()
        self.se=tk.Entry(bar,textvariable=self.sv,
                         bg=T["BG_CARD"],fg=T["TEXT_MUTED"],
                         insertbackground=T["ACCENT2"],relief="flat",
                         font=FONT_BODY,bd=0,highlightthickness=1,
                         highlightbackground=T["BORDER"],
                         highlightcolor=T["ACCENT2"],width=26)
        self.se.pack(side="left",ipady=5,padx=(0,8))
        self.se.insert(0,"Search tasks...")
        self.se.bind("<FocusIn>", lambda e:
            (self.se.delete(0,"end"),self.se.config(fg=T["TEXT_PRIMARY"]))
            if self.se.get()=="Search tasks..." else None)
        self.se.bind("<FocusOut>", lambda e:
            (self.se.insert(0,"Search tasks..."),self.se.config(fg=T["TEXT_MUTED"]))
            if not self.se.get() else None)
        self.sv.trace_add("write", lambda *_: self._filt())

        tk.Label(bar,text="Filter:",bg=T["BG_DARK"],
                 fg=T["TEXT_MUTED"],font=FONT_SMALL).pack(side="left",padx=(0,4))
        self.fv=tk.StringVar(value="All")
        ttk.Combobox(bar,textvariable=self.fv,
                     values=["All","Study","Work","Personal",
                             "OVERDUE","CRITICAL","Pending","Done"],
                     state="readonly",width=10,font=FONT_SMALL
                     ).pack(side="left",padx=(0,10))
        self.fv.trace_add("write", lambda *_: self._filt())

        # Feature 9 — Export CSV
        self._btn(bar,"📤  Export CSV",T["ACCENT2"],"white",
                  self._export).pack(side="right")

        # Tabs
        tb=tk.Frame(p,bg=T["BG_DARK"]); tb.pack(fill="x",pady=(0,4))
        for lbl,key in [("📋  Optimized Schedule","sch"),
                        ("📊  Analytics & Chart","ana"),
                        ("🔍  Algorithm Log","log")]:
            b=tk.Button(tb,text=lbl,bg=T["BG_CARD"],fg=T["TEXT_MUTED"],
                        relief="flat",font=FONT_SMALL,padx=14,pady=7,
                        cursor="hand2",command=lambda k=key:self._tab(k))
            b.pack(side="left",padx=(0,4))
            setattr(self,f"_tb_{key}",b)

        self.tc=tk.Frame(p,bg=T["BG_DARK"]); self.tc.pack(fill="both",expand=True)
        self._build_sch(); self._build_ana(); self._build_log()
        self._tab("sch")

    def _cards(self):
        for w in self.sf.winfo_children(): w.destroy()
        total = len(self.raw)
        done  = sum(1 for t in self.raw if t.get("status")=="Done")
        od    = sum(1 for t in self.opt if t.get("constraint_flag")=="OVERDUE")
        cr    = sum(1 for t in self.opt if t.get("constraint_flag")=="CRITICAL")
        th    = sum(t.get("estimated_hours",0) for t in self.raw)
        for lbl,val,col,ic in [
            ("Total",         str(total),       T["ACCENT"],  "📌"),
            ("Done",          str(done),         T["SUCCESS"], "✔"),
            ("Overdue",       str(od),           T["DANGER"],  "🔴"),
            ("Critical ≤2d",  str(cr),           T["WARNING"], "⚠️"),
            ("Total Hours",   f"{th:.1f}h",      T["ACCENT2"], "⏱️"),
        ]:
            c=tk.Frame(self.sf,bg=T["BG_CARD"],padx=12,pady=10)
            c.pack(side="left",fill="x",expand=True,padx=(0,5))
            tk.Label(c,text=f"{ic} {lbl}",bg=T["BG_CARD"],
                     fg=T["TEXT_MUTED"],font=FONT_SMALL).pack(anchor="w")
            tk.Label(c,text=val,bg=T["BG_CARD"],fg=col,
                     font=("Segoe UI",17,"bold")).pack(anchor="w")

    # ── Schedule Tab ──────────────────────────────────────────────────────────
    def _build_sch(self):
        self.f_sch=tk.Frame(self.tc,bg=T["BG_DARK"])
        tk.Label(self.f_sch,
                 text="  💡  Priority bars show AI score  •  Double-click to Edit  •  Countdown column updates daily",
                 bg=T["BG_DARK"],fg=T["TEXT_MUTED"],
                 font=FONT_SMALL,anchor="w").pack(fill="x",pady=(0,3))

        cols=("rank","name","cat","dl","cd","imp","dif","hrs","sc","bar","st")
        self.tree=ttk.Treeview(self.f_sch,columns=cols,show="headings",height=16)
        for col,hd,w,a in [
            ("rank","#",     46,"center"),("name","Task",     175,"w"),
            ("cat","Cat.",   72,"center"),("dl","Deadline",    95,"center"),
            ("cd","Days Left",72,"center"),                    # Feature 3
            ("imp","Imp.",   44,"center"),("dif","Diff.",      44,"center"),
            ("hrs","Hrs",    44,"center"),("sc","AI Score",    76,"center"),
            ("bar","Priority ▓",140,"center"),                 # Feature 2
            ("st","Status",100,"center"),
        ]:
            self.tree.heading(col,text=hd); self.tree.column(col,width=w,anchor=a)

        st=ttk.Style(); st.theme_use("clam")
        st.configure("Treeview",background=T["BG_CARD"],foreground=T["TEXT_PRIMARY"],
                     fieldbackground=T["BG_CARD"],rowheight=28,font=FONT_SMALL)
        st.configure("Treeview.Heading",background=T["BG_INPUT"],
                     foreground=T["ACCENT2"],font=("Segoe UI",9,"bold"))
        st.map("Treeview",background=[("selected",T["ACCENT"])])

        for tag,col in [("OVERDUE",T["DANGER"]),("CRITICAL",T["WARNING"]),
                        ("OVERLOAD",T["WARNING"]),("OK",T["SUCCESS"]),
                        ("DONE",T["TEXT_MUTED"])]:
            self.tree.tag_configure(tag,foreground=col)
        self.tree.tag_configure("TOP",background="#2d1f4e")

        vsb=ttk.Scrollbar(self.f_sch,orient="vertical",command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right",fill="y"); self.tree.pack(fill="both",expand=True)
        self.tree.bind("<Double-1>",lambda e:self._edit())

        ab=tk.Frame(self.f_sch,bg=T["BG_DARK"]); ab.pack(fill="x",pady=5)
        self._btn(ab,"✔  Mark Done",   T["SUCCESS"],"white",self._done).pack(side="left",padx=(0,5))
        self._btn(ab,"✏️  Edit Task",   T["ACCENT2"],"white",self._edit).pack(side="left",padx=(0,5))
        self._btn(ab,"🗑  Delete Task", T["DANGER"], "white",self._del).pack(side="left")

    # ── Analytics Tab ─────────────────────────────────────────────────────────
    def _build_ana(self):
        self.f_ana=tk.Frame(self.tc,bg=T["BG_DARK"])
        L=tk.Frame(self.f_ana,bg=T["BG_DARK"])
        R=tk.Frame(self.f_ana,bg=T["BG_CARD"])
        L.pack(side="left",fill="both",expand=True,padx=(0,6))
        R.pack(side="left",fill="both",expand=True)

        self.at=tk.Text(L,bg=T["BG_CARD"],fg=T["TEXT_PRIMARY"],
                        font=FONT_MONO,relief="flat",wrap="word",
                        padx=14,pady=12,state="disabled",highlightthickness=0)
        self.at.pack(fill="both",expand=True)

        tk.Label(R,text="📊  Priority Score Chart",bg=T["BG_CARD"],
                 fg=T["ACCENT2"],font=FONT_HEADING
                 ).pack(anchor="w",padx=12,pady=(10,4))
        self.cc=tk.Canvas(R,bg=T["BG_CARD"],highlightthickness=0)  # Feature 6
        self.cc.pack(fill="both",expand=True,padx=8,pady=(0,10))

    # ── Log Tab ───────────────────────────────────────────────────────────────
    def _build_log(self):
        self.f_log=tk.Frame(self.tc,bg=T["BG_DARK"])
        self.lt=tk.Text(self.f_log,bg=T["LOG_BG"],fg=T["ACCENT2"],
                        font=FONT_MONO,relief="flat",wrap="word",
                        padx=16,pady=14,state="disabled",highlightthickness=0)
        self.lt.pack(fill="both",expand=True)

    def _tab(self, key):
        for k in ("sch","ana","log"):
            getattr(self,f"f_{k}").pack_forget()
            getattr(self,f"_tb_{k}").config(bg=T["BG_CARD"],fg=T["TEXT_MUTED"])
        getattr(self,f"f_{key}").pack(fill="both",expand=True)
        getattr(self,f"_tb_{key}").config(bg=T["ACCENT"],fg="white")
        if key=="ana": self.after(60, self._chart)

    # ══════════════════════════════════════════════════════════════════════════
    #  FEATURE 4 — THEME TOGGLE
    # ══════════════════════════════════════════════════════════════════════════
    def _toggle_theme(self):
        self._theme = "light" if self._theme=="dark" else "dark"
        T.update(THEMES[self._theme])
        self._pc = [T["ACCENT"],"#9d4edd","#c77dff",T["ACCENT2"],"#38bdf8"]
        for w in self.winfo_children(): w.destroy()
        self._ui(); self._ai()
        self.toast.show(
            f"{'Light ☀️' if self._theme=='light' else 'Dark 🌙'} theme active","info")

    # ══════════════════════════════════════════════════════════════════════════
    #  ANIMATIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _tick(self):
        try:
            self.clk.config(text=datetime.now().strftime("📅 %d %b %Y   🕐 %H:%M:%S"))
        except: pass
        self.after(1000,self._tick)

    def _pulse(self):
        try:
            self.ttl.config(fg=self._pc[self._pi % len(self._pc)])
        except: pass
        self._pi+=1; self.after(1400,self._pulse)

    # ══════════════════════════════════════════════════════════════════════════
    #  CORE ACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _add(self):
        nm=self.en.get().strip(); dl=self.ed.get().strip()
        if not nm: self.toast.show("Task name is empty!","danger"); return
        try: datetime.strptime(dl,"%Y-%m-%d")
        except: self.toast.show("Use YYYY-MM-DD format!","danger"); return
        self.raw.append(dict(id=self._ctr,name=nm,deadline=dl,
                             importance=int(self.vi.get()),
                             difficulty=int(self.vd.get()),
                             estimated_hours=round(float(self.vh.get()),1),
                             category=self.vcat.get(),status="Pending"))
        self._ctr+=1; save(self.raw)
        self.en.delete(0,"end"); self.vi.set(3); self.vd.set(3); self.vh.set(2.0)
        orig=self.hdr.cget("bg")
        self.hdr.config(bg="#0d3b2e")
        self.after(300,lambda:self.hdr.config(bg=orig))
        self.toast.show(f"'{nm}' added & optimized! 🚀","success")
        self._ai()

    def _ai(self):
        self.opt=AIEngine.run([t.copy() for t in self.raw])
        self._rtree(); self._rana(); self._rlog(); self._cards(); self._overload()

    def _overload(self):
        ph=sum(t.get("estimated_hours",0) for t in self.raw if t.get("status")!="Done")
        if ph > AIEngine.DAILY_HOUR_CAP*3:
            self.banner_frame.pack(fill="x", after=self.hdr)
        else:
            self.banner_frame.pack_forget()

    def _rtree(self):
        self.tree.delete(*self.tree.get_children())
        smap={"OVERDUE":"🔴 Overdue","CRITICAL":"⚠️ Critical",
              "OVERLOAD":"⚡ Overload","OK":"✅ OK"}
        ri={1:"🥇",2:"🥈",3:"🥉"}
        for t in self.opt:
            if not self._ok(t): continue
            flag=t.get("constraint_flag","OK"); done=t.get("status")=="Done"
            tag="DONE" if done else ("TOP" if t["rank"]==1 else flag)
            st="✔ Done" if done else smap.get(flag,"✅ OK")
            d=t.get("days_remaining",0)
            cd="OVERDUE" if d<0 else ("⚡ TODAY!" if d==0 else f"{int(d)}d left")
            sc=t.get("priority_score",0)
            bar="█"*int(sc*10)+"░"*(10-int(sc*10))+f"  {sc:.2f}"
            self.tree.insert("","end",iid=str(t["id"]),
                values=(ri.get(t["rank"],str(t["rank"])),t["name"],
                        t.get("category","—"),t["deadline"],cd,
                        t["importance"],t["difficulty"],
                        f"{t['estimated_hours']}h",f"{sc:.3f}",bar,st),
                tags=(tag,))

    def _ok(self, t):
        s=self.sv.get().strip().lower()
        if s and s!="search tasks..." and s not in t.get("name","").lower():
            return False
        fv=self.fv.get()
        if fv=="All": return True
        if fv in ("Study","Work","Personal"): return t.get("category","")==fv
        if fv in ("OVERDUE","CRITICAL"):      return t.get("constraint_flag","")==fv
        if fv=="Done":    return t.get("status","")=="Done"
        if fv=="Pending": return t.get("status","")!="Done"
        return True

    def _filt(self): self._rtree()

    def _rana(self):
        self.at.config(state="normal"); self.at.delete("1.0","end")
        sep="═"*52
        lines=[sep,"  📊  TASK ANALYTICS",sep,""]
        if not self.opt:
            lines.append("  No tasks yet. Add some to get started!")
        else:
            cats={}
            for t in self.raw: cats[t.get("category","Other")]=cats.get(t.get("category","Other"),0)+1
            lines+=["  📁  CATEGORY BREAKDOWN","  "+"─"*44]
            for c,n in sorted(cats.items(),key=lambda x:-x[1]):
                p=n/len(self.raw)*100
                lines.append(f"  {c:<12} {'█'*int(p/5)}{'░'*(20-int(p/5))}  {n} ({p:.0f}%)")
            th=sum(t["estimated_hours"] for t in self.raw)
            dh=sum(t["estimated_hours"] for t in self.raw if t.get("status")=="Done")
            rm=th-dh
            lines+=["","  ⏱️  WORKLOAD","  "+"─"*44,
                    f"  Total      : {th:.1f}h",
                    f"  Completed  : {dh:.1f}h",
                    f"  Remaining  : {rm:.1f}h",
                    f"  Days Needed: {rm/10:.1f}  (@ 10h/day)",
                    f"  Load Status: {'⚠️ HIGH' if rm>30 else '✅ MANAGEABLE'}"]
            lines+=["","  🏆  TOP 3  (Greedy Selection)","  "+"─"*44]
            for t in self.opt[:3]:
                lines.append(f"  {['🥇','🥈','🥉'][t['rank']-1]}  {t['name'][:30]:<30}  {t['priority_score']:.3f}")
            fl=[t for t in self.opt if t["constraint_flag"]!="OK"]
            lines+=["","  🔴  CSP CONSTRAINT FLAGS","  "+"─"*44]
            if fl:
                for t in fl:
                    lines.append(f"  [{t['constraint_flag']:<8}]  {t['name'][:28]}  {t['deadline']}")
            else:
                lines.append("  ✅  All constraints satisfied!")
        lines+=["",sep]
        self.at.insert("1.0","\n".join(lines))
        self.at.config(state="disabled")

    # Feature 6 — Canvas bar chart
    def _chart(self):
        c=self.cc; c.delete("all")
        if not self.opt:
            c.create_text(10,10,text="No tasks yet.",anchor="nw",
                          fill=T["TEXT_MUTED"],font=FONT_SMALL); return
        c.update_idletasks()
        W=c.winfo_width() or 320; H=c.winfo_height() or 360
        tasks=self.opt[:10]; n=len(tasks)
        if not n: return
        ms=max(t["priority_score"] for t in tasks) or 1
        pl,pr,pt,pb=95,28,18,30
        cw=W-pl-pr; rt=(H-pt-pb)/n
        bh=rt*0.68
        cols=[T["ACCENT"],T["ACCENT2"],T["SUCCESS"],T["WARNING"],
              "#a78bfa","#34d399","#f87171","#60a5fa","#fbbf24","#c084fc"]
        for i,t in enumerate(tasks):
            y1=pt+i*rt; y2=y1+bh; mid=(y1+y2)/2
            c.create_rectangle(pl,y1,pl+cw,y2,fill=T["BG_INPUT"],outline="")
            fw=(t["priority_score"]/ms)*cw
            col=cols[i%len(cols)]
            if t.get("constraint_flag")=="OVERDUE":  col=T["DANGER"]
            elif t.get("constraint_flag")=="CRITICAL": col=T["WARNING"]
            c.create_rectangle(pl,y1,pl+fw,y2,fill=col,outline="")
            c.create_line(pl,y1+2,pl+fw,y1+2,fill="white",width=1)
            nm=t["name"][:14]+("…" if len(t["name"])>14 else "")
            c.create_text(pl-6,mid,text=nm,anchor="e",
                          fill=T["TEXT_PRIMARY"],font=("Segoe UI",8))
            c.create_text(pl+fw+5,mid,text=f"{t['priority_score']:.3f}",
                          anchor="w",fill=T["TEXT_MUTED"],font=("Consolas",8))
            if t["rank"]<=3:
                c.create_text(pl+cw-4,mid,
                              text={1:"🥇",2:"🥈",3:"🥉"}[t["rank"]],
                              anchor="e",font=("Segoe UI",10))
        c.create_text(pl+cw//2,H-10,
                      text="AI Priority Score →",
                      fill=T["TEXT_MUTED"],font=("Segoe UI",8))

    def _rlog(self):
        self.lt.config(state="normal"); self.lt.delete("1.0","end")
        sep="═"*64
        lines=[sep,"  🔍  ALGORITHM EXECUTION LOG",sep,"",
               f"  Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
               f"  Tasks     : {len(self.raw)}",""]
        if self.opt:
            lines+=["  ─── STEP 1: PREPROCESSING ─────────────────────────────────",
                    "  "+"─"*58]
            for t in self.opt:
                u=AIEngine.urgency(t.get("days_remaining",0))
                lines+=[f"  Task : {t['name'][:36]:<36}",
                        f"    Days Remaining = {t.get('days_remaining',0):.0f}",
                        f"    Urgency        = {u:.4f}   [ e^(−d/7) ]",""]
            lines+=["","  ─── STEP 2: HEURISTIC SCORING ──────────────────────────────",
                    "  "+"─"*58,
                    "  P = 0.4·Imp + 0.3·Urgency + 0.2·Diff − 0.1·Time",""]
            for t in self.opt:
                lines.append(f"  #{t['rank']:>2}  {t['name'][:34]:<34}  {t['priority_score']:.4f}")
            lines+=["","  ─── STEP 3: CONSTRAINT SATISFACTION (CSP) ──────────────────",
                    "  "+"─"*58]
            fi={"OVERDUE":"🔴","CRITICAL":"⚠️","OVERLOAD":"⚡","OK":"✅"}
            for t in self.opt:
                lines.append(f"  {fi.get(t['constraint_flag'],'✅')}  {t['name'][:34]:<34}  {t['constraint_flag']}")
            lines+=["","  ─── STEP 4: GREEDY OPTIMIZATION ────────────────────────────",
                    "  "+"─"*58,
                    "  Always pick highest-score task → O(n log n)",
                    "  Near-optimal execution schedule generated.","",
                    "  ✔  Pipeline complete!"]
        lines+=["",sep]
        self.lt.insert("1.0","\n".join(lines))
        self.lt.config(state="disabled")

    # ── Task actions ──────────────────────────────────────────────────────────
    def _done(self):
        sel=self.tree.selection()
        if not sel: self.toast.show("Select a task!","warning"); return
        tid=int(sel[0])
        nm=next((t["name"] for t in self.raw if t["id"]==tid),"Task")
        for t in self.raw:
            if t["id"]==tid: t["status"]="Done"
        save(self.raw)
        self.toast.show(f"'{nm}' completed! 🎉","success")
        self.confetti.burst()    # 🎊 Feature 10
        self._ai()

    def _edit(self):
        sel=self.tree.selection()
        if not sel: self.toast.show("Select a task!","warning"); return
        tid=int(sel[0])
        task=next((t for t in self.raw if t["id"]==tid),None)
        if not task: return
        def cb(updated):
            for i,t in enumerate(self.raw):
                if t["id"]==updated["id"]: self.raw[i]=updated
            save(self.raw)
            self.toast.show("Task updated!","info")
            self._ai()
        EditDialog(self, task, cb)

    def _del(self):
        sel=self.tree.selection()
        if not sel: self.toast.show("Select a task!","warning"); return
        if messagebox.askyesno("Delete","Delete selected task?"):
            tid=int(sel[0])
            nm=next((t["name"] for t in self.raw if t["id"]==tid),"Task")
            self.raw=[t for t in self.raw if t["id"]!=tid]
            save(self.raw)
            self.toast.show(f"'{nm}' deleted.","danger")
            self._ai()

    def _clr(self):
        if self.raw and messagebox.askyesno("Clear","Delete ALL tasks?"):
            self.raw=[]; self.opt=[]
            save(self.raw)
            self.toast.show("All tasks cleared.","warning")
            self._ai()

    def _export(self):
        if not self.opt: self.toast.show("No tasks to export!","warning"); return
        fn=f"schedule_{date.today()}.csv"
        path=os.path.join(_HERE,fn)
        flds=["rank","name","category","deadline","importance","difficulty",
              "estimated_hours","priority_score","constraint_flag","status"]
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=flds,extrasaction="ignore")
            w.writeheader(); w.writerows(self.opt)
        self.toast.show(f"Saved → {fn}","success")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
import { useState, useEffect } from "react";
import * as React from "react";
import { type Lead } from "@/src/lib/groq";
import { toast, Toaster } from "sonner";
import {
  Search, Sparkles, Menu, X
} from "lucide-react";
import * as XLSX from "xlsx";
import { GenerateLeads } from "./components/GenerateLeads";
import { API_BASE_URL } from "./apiConfig";

export default function App() {
  const [savingDB, setSavingDB] = useState(false);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeads, setSelectedLeads] = useState<Set<number>>(new Set());
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Lock body scroll when mobile sidebar drawer is open
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [sidebarOpen]);

  const exportToExcel = () => {
    if (leads.length === 0) return;

    const cleanedLeads = leads.map(lead => ({
      srNo: lead.srNo,
      name: lead.name || "",
      title: lead.title || "",
      company: lead.company || "",
      email: lead.email || "",
      phone: lead.phone || "",
      location: lead.location || "",
      website: lead.website || "",
      linkedIn: lead.linkedIn || lead.linkedin || "",
      segment: lead.segment || "",
      priority: lead.priority || "",
      channel: lead.channel || ""
    }));

    const worksheet = XLSX.utils.json_to_sheet(cleanedLeads, {
      header: ["srNo", "name", "title", "company", "email", "phone", "location", "website", "linkedIn", "segment", "priority", "channel"]
    });
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Leads");
    XLSX.writeFile(workbook, "B2B_Leads.xlsx");
    toast.success("Leads exported to Excel!");
  };

  const saveToDatabase = async () => {
    if (leads.length === 0) return;
    setSavingDB(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/save-leads`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ leads }),
      });

      if (!response.ok) throw new Error("Database save failed");
      const data = await response.json();
      if (data.leads) {
        setLeads(data.leads.map((l: any, idx: number) => ({ ...l, srNo: idx + 1 })));
      }
      toast.success(`Saved ${data.count} leads to Database!`);
    } catch (error) {
      toast.error("Failed to save leads to Database.");
      console.error(error);
    } finally {
      setSavingDB(false);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search-input')?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen text-[#1A1A24] font-medium font-sans selection:bg-[#6B2BFF]/20 flex flex-col items-stretch overflow-hidden bg-[#FAFAFD] relative">
      <Toaster position="top-right" />

      {/* Abstract background blobs */}
      <div
        className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#6B2BFF]/10 rounded-full blur-[100px] pointer-events-none will-change-[transform,filter]"
      />
      <div
        className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-[#A880FF]/10 rounded-full blur-[100px] pointer-events-none will-change-[transform,filter]"
      />

      {/* TOP NAVBAR */}
      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-[#E8E8F2] w-full px-6 py-3 flex items-center justify-between shrink-0 will-change-transform">
        <div className="flex items-center gap-3">
          {/* Mobile Sidebar Hamburger Menu Button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 -ml-1 rounded-lg hover:bg-slate-100 text-[#5A5A6D] md:hidden transition-colors"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#6B2BFF] to-[#8C5DFF] flex items-center justify-center shadow-sm">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-[#111118] leading-tight">LeadGen AI</h1>
          </div>
        </div>

        <div className="flex items-center gap-4 justify-end">
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#6B2BFF] to-[#D0B8FF] flex items-center justify-center text-[10px] font-bold text-white border-2 border-white shadow-sm">
            BB
          </div>
        </div>
      </header>

      {/* Body with Sidebar and Main */}
      <div className="flex-1 flex overflow-hidden z-10 relative mt-0.5">
        {/* Sidebar mobile overlay backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-[#111118]/40 backdrop-blur-sm z-40 md:hidden animate-in fade-in duration-200"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* SIDEBAR */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 w-[260px] bg-white md:bg-white/80 md:backdrop-blur-md border-r border-[#E8E8F2]/60 p-5 flex flex-col gap-2 shrink-0 shadow-2xl md:shadow-[4px_0_24px_rgba(0,0,0,0.02)] md:static md:translate-x-0 transition-transform duration-300 ease-in-out will-change-transform ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
          <div className="flex items-center justify-between mb-4 px-2">
            <span className="text-[11px] font-bold text-[#8A8AA3] uppercase tracking-widest">Navigation</span>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1 rounded-md hover:bg-slate-100 text-[#5A5A6D] md:hidden transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setSidebarOpen(false)}
            className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[13px] font-semibold bg-[#111118] text-white shadow-md shadow-[#111118]/20 transition-all"
          >
            <Search className="w-4 h-4" /> Generate Leads
          </button>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto flex flex-col custom-scroll">
          <div className="max-w-[1600px] w-full mx-auto px-8 py-8 flex flex-col h-full gap-8">
            <div className="flex flex-col h-full gap-6">
              <GenerateLeads
                leads={leads}
                setLeads={setLeads}
                selectedLeads={selectedLeads}
                setSelectedLeads={setSelectedLeads}
                saveToDatabase={saveToDatabase}
                exportToExcel={exportToExcel}
                savingDB={savingDB}
              />
            </div>
          </div>
        </main>
      </div>

      {/* Custom Styles for styling scrollbars and inputs */}
      <style>{`
        .custom-scroll::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .custom-scroll::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scroll::-webkit-scrollbar-thumb {
          background: #D2D2E0;
          border-radius: 10px;
        }
        .custom-scroll::-webkit-scrollbar-thumb:hover {
          background: #A0A0B2;
        }
        ::selection {
          background: rgba(107, 43, 255, 0.2);
          color: inherit;
        }
      `}</style>
    </div>
  );
}

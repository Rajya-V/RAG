
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  ArrowRight,
  BookOpen,
  Check,
  FileSearch,
  FileText,
  FileUp,
  LockKeyhole,
  Search,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  LoaderCircle,
  Plus,
  MessageSquare,
  Send,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
  X,
} from "lucide-react";
import { api } from "./api";
import "./App.css";

function sourcesOf(data) {
  if (!data) return [];

  for (const key of [
    "sources",
    "source_documents",
    "retrieved_documents",
    "results",
    "documents",
    "context",
  ]) {
    if (Array.isArray(data[key])) return data[key];
  }

  return [];
}

function answerOf(data) {
  if (typeof data === "string") return data;

  const answer =
    data?.answer ??
    data?.response ??
    data?.generated_answer ??
    data?.result;

  return typeof answer === "string"
    ? answer
    : answer?.text || answer?.content || data?.message || "";
}

function Source({ item, i }) {
  const name =
    item.filename ||
    item.file_name ||
    item.source ||
    item.document_name ||
    `Source ${i + 1}`;

  const startPage =
    item.start_page ??
    item.metadata?.start_page ??
    item.page ??
    item.page_number ??
    item.metadata?.page;

  const endPage = item.end_page ?? item.metadata?.end_page;

  const excerpt =
    item.text ||
    item.content ||
    item.page_content ||
    item.excerpt ||
    "";

  const pageLabel =
    startPage == null
      ? null
      : endPage != null && endPage !== startPage
        ? `Pages ${startPage}–${endPage}`
        : `Page ${startPage}`;

  return (
    <article className="source" key={item.chunk_id || item.id || i}>
      <FileText size={17} />
      <div className="source-content">
        <div className="source-title">
          <b>{name}</b>
          {pageLabel && <small>{pageLabel}</small>}
        </div>
        {excerpt && <p>{excerpt}</p>}
      </div>
    </article>
  );
}

function MessageContent({ content }) {
  return (
    <div className="chat-message-text">
      <ReactMarkdown>{content || ""}</ReactMarkdown>
    </div>
  );
}
export default function App() {
  const [status, setStatus] = useState("checking");

  // Uploaded documents
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [uploadErr, setUploadErr] = useState("");
  const [uploadNotice, setUploadNotice] = useState("");
  const fileInput = useRef(null);

  // Chat history
  const [chats, setChats] = useState(() => [
    {
      id: Date.now(),
      title: "New conversation",
      messages: [],
    },
  ]);
  const [activeChatId, setActiveChatId] = useState(
    () => Date.now()
  );

  // Chat composer
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState("3");
  const [asking, setAsking] = useState(false);
  const [askErr, setAskErr] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Search mode
  const [mode, setMode] = useState("chat");
  const [term, setTerm] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchErr, setSearchErr] = useState("");

  const messagesEndRef = useRef(null);
  const composerRef = useRef(null);

  const activeChat =
    chats.find((chat) => chat.id === activeChatId) || chats[0];

  const messages = activeChat?.messages || [];

  useEffect(() => {
    api.health()
      .then(() => setStatus("ready"))
      .catch(() => setStatus("offline"));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, asking]);

  function updateActiveChat(updater) {
    setChats((previous) =>
      previous.map((chat) =>
        chat.id === activeChatId ? updater(chat) : chat
      )
    );
  }

  function newChat() {
    const id = Date.now() + Math.random();

    setChats((previous) => [
      ...previous,
      {
        id,
        title: "New conversation",
        messages: [],
      },
    ]);

    setActiveChatId(id);
    setQuestion("");
    setAskErr("");
    setMode("chat");
    setSearchResults(null);
  }

  function deleteChat(id) {
    setChats((previous) => {
      const remaining = previous.filter((chat) => chat.id !== id);

      if (remaining.length === 0) {
        const fresh = {
          id: Date.now() + Math.random(),
          title: "New conversation",
          messages: [],
        };

        setActiveChatId(fresh.id);
        return [fresh];
      }

      if (activeChatId === id) {
        setActiveChatId(remaining[0].id);
      }

      return remaining;
    });
  }

  function toggleDocument(id) {
    setSelectedIds((previous) =>
      previous.includes(id)
        ? previous.filter((item) => item !== id)
        : [...previous, id]
    );
  }

  function chooseFiles(fileList) {
    setUploadErr("");
    setUploadNotice("");

    const files = Array.from(fileList || []);

    if (!files.length) return;

    const validFiles = [];
    const errors = [];

    for (const file of files) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        errors.push(`${file.name}: only PDF files are supported.`);
      } else if (file.size === 0) {
        errors.push(`${file.name}: the file is empty.`);
      } else if (file.size > 10 * 1024 * 1024) {
        errors.push(`${file.name}: exceeds the 10 MB limit.`);
      } else if (
        documents.some(
          (doc) =>
            doc.filename.toLowerCase() === file.name.toLowerCase()
        )
      ) {
        errors.push(`${file.name}: already uploaded.`);
      } else if (
        validFiles.some(
          (item) =>
            item.name.toLowerCase() === file.name.toLowerCase()
        )
      ) {
        errors.push(`${file.name}: selected more than once.`);
      } else {
        validFiles.push(file);
      }
    }

    if (errors.length) {
      setUploadErr(errors.join(" "));
    }

    if (validFiles.length) {
      uploadFiles(validFiles);
    }
  }

  async function uploadFiles(files) {
    setUploading(true);
    setUploadNotice("");
    setUploadErr("");

    const successes = [];
    const errors = [];

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        setUploadProgress(
          `Processing ${i + 1} of ${files.length}: ${file.name}`
        );

        try {
          const result = await api.upload(file);

          if (!result.document_id) {
            throw new Error("The server did not return a document ID.");
          }

          successes.push({
            id: result.document_id,
            filename: result.filename || file.name,
            pageCount: result.page_count ?? null,
            chunkCount: result.chunk_count ?? null,
          });
        } catch (error) {
          errors.push(`${file.name}: ${error.message || "Upload failed."}`);
        }
      }

      if (successes.length) {
        setDocuments((previous) => {
          const knownIds = new Set(previous.map((doc) => doc.id));

          return [
            ...previous,
            ...successes.filter((doc) => !knownIds.has(doc.id)),
          ];
        });

        setSelectedIds((previous) => [
          ...new Set([
            ...previous,
            ...successes.map((doc) => doc.id),
          ]),
        ]);

        setStatus("ready");

        setUploadNotice(
          `Successfully processed ${successes.length} PDF${
            successes.length === 1 ? "" : "s"
          }.`
        );
      }

      if (errors.length) {
        setUploadErr(errors.join("\n"));
      }
    } finally {
      setUploading(false);
      setUploadProgress("");
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function ask(e) {
    e.preventDefault();

    const query = question.trim();

    if (!query || asking) return;

    if (!documents.length) {
      setAskErr("Upload at least one PDF before asking a question.");
      return;
    }

    if (!selectedIds.length) {
      setAskErr("Select at least one PDF in the sidebar.");
      return;
    }

    const chatId = activeChatId;
    const previousMessages = messages;

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: query,
    };

    const history = previousMessages
      .filter((message) =>
        ["user", "assistant"].includes(message.role)
      )
      .slice(-8)
      .map(({ role, content }) => ({ role, content }));

    setQuestion("");
    setAsking(true);
    setAskErr("");
    setMode("chat");

    setChats((previous) =>
      previous.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              title:
                chat.messages.length === 0
                  ? query.slice(0, 42) +
                    (query.length > 42 ? "…" : "")
                  : chat.title,
              messages: [...chat.messages, userMessage],
            }
          : chat
      )
    );

    try {
      const response = await api.ask({
        query,
        top_k: Number(topK),
        document_ids: selectedIds,
        conversation_history: history,
      });

      const assistantMessage = {
        id: Date.now() + Math.random(),
        role: "assistant",
        content: answerOf(response) || "No answer was returned.",
        sources: sourcesOf(response),
      };

      setChats((previous) =>
        previous.map((chat) =>
          chat.id === chatId
            ? {
                ...chat,
                messages: [...chat.messages, assistantMessage],
              }
            : chat
        )
      );

      setStatus("ready");
    } catch (error) {
      setAskErr(error.message || "Could not get an answer.");
    } finally {
      setAsking(false);
      composerRef.current?.focus();
    }
  }

  async function search(e) {
    e.preventDefault();

    if (!term.trim() || searching) return;

    setSearching(true);
    setSearchErr("");
    setSearchResults(null);

    try {
      const response = await api.search({
        query: term.trim(),
        top_k: Number(topK),
        document_id: null,
      });

      setSearchResults(response);
      setStatus("ready");
    } catch (error) {
      setSearchErr(error.message || "Search failed.");
    } finally {
      setSearching(false);
    }
  }

  return (
    <main className="shell">
      {/* Existing landing-page header */}
      <header className="header">
        <a className="brand" href="#top">
          <span className="logo"><BookOpen size={21} /></span>
          knowledge<span className="light">copilot</span>
        </a>

        <nav>
          <a href="#workspace">Workspace</a>
          <a href="#about">About</a>
        </nav>

        <span className={`status ${status === "offline" ? "offline" : ""}`}>
          <i />
          {status === "checking"
            ? "Connecting…"
            : status === "ready"
              ? "Local · Ready"
              : "API offline"}
        </span>
      </header>

      {/* Existing hero — preserved */}
      <section className="hero" id="top">
        <div className="hero-copy">
          <div className="eyebrow">
            <span /> YOUR KNOWLEDGE, IN FOCUS
          </div>

          <h1>
            Turn your documents
            <br />
            into <em>answers.</em>
          </h1>

          <p className="lead">
            A quieter, smarter way to work with your PDFs. Ask questions,
            explore sources, and find the details that matter.
          </p>

          <div className="hero-actions">
            <a className="btn primary" href="#workspace">
              Start exploring <ArrowRight size={16} />
            </a>
            <a className="underlink" href="#about">
              Discover how it works ↘
            </a>
          </div>

          <div className="trust">
            <span><ShieldCheck size={15} /> Source-grounded answers</span>
            <span><LockKeyhole size={15} /> Local-first workflow</span>
          </div>
        </div>

        <div className="art">
          <div className="orbit one" />
          <div className="orbit two" />

          <div className="label-float">
            <Sparkles size={14} /> Knowledge, connected
          </div>

          <div className="paper back">
            <div className="redline" />
            <div className="line wide" />
            <div className="line" />
            <div className="line short" />
            <div className="bars">
              <i /><i /><i /><i /><i />
            </div>
          </div>

          <div className="paper front">
            <small>PDF　 /　 RESEARCH NOTES</small>
            <h3>Quarterly<br />insights report</h3>
            <div className="line wide" />
            <div className="line" />
            <div className="line short" />
            <footer>12 pages <span>Updated today</span></footer>
          </div>

          <div className="answer-float">
            <small><Sparkles size={13} /> AN ANSWER, FOUND</small>
            <p>
              “The strongest trend is a steady improvement across the key
              indicators…”
            </p>
            <div>
              <FileText size={13} /> Research notes.pdf <b>p. 04</b>
            </div>
          </div>

          <div className="stamp">READ<br />BETWEEN<br />THE LINES.</div>
        </div>
      </section>

      {/* Existing introduction — preserved */}
      <section className="intro">
        <b><span>01 /</span> Bring your knowledge together.</b>
        <p>One simple workspace for the documents you rely on.</p>
      </section>

      {/* Workspace */}
      <section className="workspace" id="workspace">
        <div className="section-head">
          <div>
            <div className="eyebrow"><span /> THE WORKSPACE</div>
            <h2>
              Make every page
              <br />
              <em>more useful.</em>
            </h2>
          </div>
          <p>
            Start with a document. Ask a question. Follow the evidence
            wherever it leads.
          </p>
        </div>

        <div className={`copilot-workspace ${sidebarOpen ? "" : "sidebar-collapsed"}`}>
          {/* Sidebar */}
          <aside className="copilot-sidebar">
            <button className="btn primary full" onClick={newChat}>
              <Plus size={17} /> New chat
            </button>

            <div className="sidebar-label">WORKSPACE</div>

            <div className="mode-switch">
              <button
                className={mode === "chat" ? "active" : ""}
                onClick={() => setMode("chat")}
              >
                <MessageSquare size={16} /> Chat
              </button>

              <button
                className={mode === "search" ? "active" : ""}
                onClick={() => setMode("search")}
              >
                <Search size={16} /> Search
              </button>
            </div>

            <div className="sidebar-label">YOUR DOCUMENTS</div>

            <button
              className="sidebar-upload"
              onClick={() => fileInput.current?.click()}
              disabled={uploading}
            >
              <FileUp size={16} />
              <span>Add PDF files</span>
              <Plus size={15} />
            </button>

            <input
              ref={fileInput}
              hidden
              type="file"
              multiple
              accept=".pdf,application/pdf"
              onChange={(e) => chooseFiles(e.target.files)}
            />

            <div className="document-list">
              {documents.length === 0 && (
                <p className="sidebar-empty">
                  Your uploaded PDFs will appear here.
                </p>
              )}

              {documents.map((doc) => (
                <label className="document-item" key={doc.id}>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(doc.id)}
                    onChange={() => toggleDocument(doc.id)}
                  />

                  <FileText size={16} />

                  <span title={doc.filename}>
                    {doc.filename}
                    {doc.pageCount != null && (
                      <small>{doc.pageCount} pages</small>
                    )}
                  </span>
                </label>
              ))}
            </div>

            {documents.length > 0 && (
              <div className="document-selection">
                {selectedIds.length} of {documents.length} selected
                <button
                  type="button"
                  onClick={() =>
                    setSelectedIds(
                      selectedIds.length === documents.length
                        ? []
                        : documents.map((doc) => doc.id)
                    )
                  }
                >
                  {selectedIds.length === documents.length
                    ? "Clear"
                    : "Select all"}
                </button>
              </div>
            )}

            <div className="sidebar-label history-label">RECENT CHATS</div>

            <div className="chat-history">
              {chats
                .slice()
                .reverse()
                .map((chat) => (
                  <div
                    key={chat.id}
                    className={`history-item ${
                      chat.id === activeChatId ? "active" : ""
                    }`}
                  >
                    <button
                      className="history-select"
                      onClick={() => {
                        setActiveChatId(chat.id);
                        setMode("chat");
                        setAskErr("");
                      }}
                      title={chat.title}
                    >
                      <MessageSquare size={15} />
                      <span>{chat.title}</span>
                    </button>

                    {chats.length > 1 && (
                      <button
                        className="history-delete"
                        title="Delete conversation"
                        aria-label={`Delete ${chat.title}`}
                        onClick={() => deleteChat(chat.id)}
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                ))}
            </div>

            <div className="sidebar-bottom">
              <LockKeyhole size={14} />
              <span>Local-first workflow</span>
            </div>
          </aside>

          {/* Main chat panel */}

          <div className="copilot-main">
            <div className="copilot-toolbar">
              <button
                className="icon-button"
                title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
                onClick={() => setSidebarOpen((open) => !open)}
              >
                {sidebarOpen
                  ? <PanelLeftClose size={18} />
                  : <PanelLeftOpen size={18} />}
              </button>

              <div className="toolbar-title">
                <b>{mode === "chat" ? activeChat?.title : "Search documents"}</b>
                <small>
                  {selectedIds.length} PDF{selectedIds.length === 1 ? "" : "s"} selected
                </small>
              </div>

              <label className="topk-control">
                <span>Sources</span>
                <select
                  value={topK}
                  onChange={(e) => setTopK(e.target.value)}
                >
                  <option value="1">1</option>
                  <option value="3">3</option>
                  <option value="5">5</option>
                  <option value="10">10</option>
                </select>
              </label>
            </div>

            {uploading && (
              <div className="workspace-notice">
                <LoaderCircle size={16} className="spin" />
                {uploadProgress || "Processing PDFs…"}
              </div>
            )}

            {uploadNotice && (
              <div className="workspace-notice success-notice">
                <Check size={16} /> {uploadNotice}
                <button
                  className="notice-close"
                  onClick={() => setUploadNotice("")}
                  aria-label="Dismiss notification"
                >
                  <X size={15} />
                </button>
              </div>
            )}

            {uploadErr && (
              <div className="workspace-notice error-notice" role="alert">
                {uploadErr}
                <button
                  className="notice-close"
                  onClick={() => setUploadErr("")}
                  aria-label="Dismiss error"
                >
                  <X size={15} />
                </button>
              </div>
            )}

            {mode === "chat" ? (
              <>
                <div className="chat-scroll">
                  {messages.length === 0 ? (
                    <div className="chat-welcome">
                      <span className="welcome-icon">
                        <Sparkles size={23} />
                      </span>
                      <h3>What would you like to understand?</h3>
                      <p>
                        Ask questions about your PDFs. Answers use retrieved
                        document passages, with sources to help you verify them.
                      </p>

                      {documents.length === 0 ? (
                        <button
                          className="btn outline"
                          onClick={() => fileInput.current?.click()}
                        >
                          <UploadCloud size={17} /> Upload your first PDF
                        </button>
                      ) : (
                        <div className="suggestion-list">
                          {[
                            "Summarize the key points.",
                            "What are the main findings?",
                            "What evidence supports the conclusions?",
                          ].map((suggestion) => (
                            <button
                              key={suggestion}
                              onClick={() => setQuestion(suggestion)}
                            >
                              {suggestion} <ArrowRight size={15} />
                            </button>
                          ))}
                        </div>
                      )}

                      {documents.length > 0 && (
                        <p className="selected-hint">
                          {selectedIds.length
                            ? `${selectedIds.length} PDF${
                                selectedIds.length === 1 ? "" : "s"
                              } selected for this chat.`
                            : "Select one or more PDFs in the sidebar to begin."}
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="message-list">
                      {messages.map((message) => (
                        <article
                          key={message.id}
                          className={`chat-message ${message.role}`}
                        >
                          <div className="message-avatar">
                            {message.role === "user"
                              ? "You"
                              : <Sparkles size={17} />}
                          </div>

                          <div className="message-body">
                            <div className="message-author">
                              {message.role === "user"
                                ? "You"
                                : "Knowledge Copilot"}
                            </div>

                            <MessageContent content={message.content} />

                            
                          </div>
                        </article>
                      ))}

                      {asking && (
                        <div className="chat-message assistant">
                          <div className="message-avatar">
                            <Sparkles size={17} />
                          </div>
                          <div className="message-body">
                            <div className="message-author">
                              Knowledge Copilot
                            </div>
                            <div className="thinking-indicator">
                              <LoaderCircle size={17} className="spin" />
                              Reading your documents…
                            </div>
                          </div>
                        </div>
                      )}

                      <div ref={messagesEndRef} />
                    </div>
                  )}
                </div>

                <div className="composer-area">
                  {askErr && (
                    <p className="error composer-error" role="alert">
                      {askErr}
                    </p>
                  )}

                  <form className="chat-composer" onSubmit={ask}>
                    <textarea
                      ref={composerRef}
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyDown={(e) => {
                        if (
                          e.key === "Enter" &&
                          !e.shiftKey &&
                          !e.nativeEvent.isComposing
                        ) {
                          e.preventDefault();
                          e.currentTarget.form?.requestSubmit();
                        }
                      }}
                      maxLength={1000}
                      rows={2}
                      placeholder="Ask anything about your documents…"
                      aria-label="Ask a question about your documents"
                      disabled={asking}
                    />

                    <div className="composer-footer">
                      <span>
                        <LockKeyhole size={13} />
                        Answers grounded in selected PDFs
                      </span>

                      <div className="composer-actions">
                        <small>{question.length}/1000</small>
                        <button
                          className="send-button"
                          type="submit"
                          disabled={
                            !question.trim() ||
                            asking ||
                            !documents.length ||
                            !selectedIds.length
                          }
                          aria-label="Send message"
                          title="Send message"
                        >
                          {asking
                            ? <LoaderCircle size={18} className="spin" />
                            : <Send size={18} />}
                        </button>
                      </div>
                    </div>
                  </form>

                  <p className="composer-disclaimer">
                    Verify important details against the cited source pages.
                  </p>
                </div>
              </>
            ) : (
              <div className="search-panel">
                <div className="search-panel-intro">
                  <span className="welcome-icon">
                    <FileSearch size={22} />
                  </span>
                  <h3>Search your knowledge</h3>
                  <p>
                    Find relevant passages across your indexed documents.
                  </p>
                </div>

                <form className="workspace-search-form" onSubmit={search}>
                  <Search size={18} />
                  <input
                    value={term}
                    onChange={(e) => setTerm(e.target.value)}
                    placeholder="Search for a concept or phrase…"
                    required
                  />
                  <button
                    type="submit"
                    className="btn primary"
                    disabled={!term.trim() || searching}
                  >
                    {searching
                      ? <LoaderCircle size={16} className="spin" />
                      : <Search size={16} />}
                    Search
                  </button>
                </form>

                {searchErr && (
                  <p className="error" role="alert">{searchErr}</p>
                )}

                {searchResults && (
                  <div className="workspace-search-results">
                    <h4>
                      Search results
                      <span>{sourcesOf(searchResults).length}</span>
                    </h4>

                    {sourcesOf(searchResults).length === 0 ? (
                      <p>No matching passages were returned.</p>
                    ) : (
                      sourcesOf(searchResults).map((source, index) => (
                        <Source
                          key={source.chunk_id || source.id || index}
                          item={source}
                          i={index}
                        />
                      ))
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Existing About section — preserved */}
      <section className="principles" id="about">
        <div>
          <div className="eyebrow"><span /> BUILT WITH INTENTION</div>
          <h2>
            Less searching.
            <br />
            <em>More understanding.</em>
          </h2>
        </div>

        <div>
          <span className="principle-icon"><LockKeyhole size={18} /></span>
          <h4>Local-first</h4>
          <p>
            Designed around a local-first workflow. Deployment determines
            where data is processed.
          </p>
        </div>

        <div>
          <span className="principle-icon"><BookOpen size={18} /></span>
          <h4>Evidence included</h4>
          <p>
            Trace answers to document passages and page references when
            available.
          </p>
        </div>

        <div>
          <span className="principle-icon"><Search size={18} /></span>
          <h4>Search that connects</h4>
          <p>
            Combine semantic meaning with keyword matches to find useful
            context.
          </p>
        </div>
      </section>

      {/* Existing footer — preserved */}
      <footer className="footer">
        <a className="brand" href="#top">
          <span className="logo"><BookOpen size={18} /></span>
          knowledge<span className="light">copilot</span>
        </a>
        <span>Thoughtful answers begin with good sources.</span>
        <a href="#top">Back to top ↑</a>
      </footer>
    </main>
  );
}

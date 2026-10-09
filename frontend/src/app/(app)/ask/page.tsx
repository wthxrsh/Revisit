"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  MessagesSquare,
  PanelLeft,
  Plus,
  Quote,
  Send,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";

import { api, ApiError } from "@/lib/api";
import type {
  ChatMessage,
  Citation,
  Conversation,
  Document,
} from "@/lib/types";
import { cn, timeAgo, titleFromQuestion } from "@/lib/utils";
import { Badge, Button, IconButton, Spinner, Textarea } from "@/components/ui";
import { LogoMark } from "@/components/logo";
import { useToast } from "@/components/toast";

const EXAMPLES = [
  "Summarize the key ideas across my documents.",
  "What do my notes say about retrieval augmented generation?",
  "List any action items or open questions I captured.",
];

let localIdCounter = 0;
function createLocalId(prefix: string): string {
  localIdCounter += 1;
  return `${prefix}-${localIdCounter}`;
}

function citationLabel(citation: Citation): string {
  const page =
    citation.page_number !== null ? ` · p.${citation.page_number}` : "";
  return `${citation.filename}${page}`;
}

function CitationList({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState<number | null>(null);

  if (citations.length === 0) return null;

  return (
    <div className="mt-3 space-y-1.5">
      <div className="flex flex-wrap gap-1.5">
        {citations.map((citation, index) => {
          const active = open === index;
          return (
            <button
              key={`${citation.chunk_id ?? citation.chunk_index}-${index}`}
              type="button"
              onClick={() => setOpen(active ? null : index)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-lg border px-2 py-1 text-[11px] transition-colors",
                active
                  ? "border-accent/50 bg-accent/10 text-accent"
                  : "border-line bg-white/[0.03] text-muted hover:text-ink",
              )}
            >
              <Quote className="h-3 w-3" />
              {citationLabel(citation)}
            </button>
          );
        })}
      </div>
      <AnimatePresence initial={false}>
        {open !== null && citations[open] ? (
          <motion.blockquote
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden rounded-xl border border-line bg-white/[0.02] px-3 py-2 text-xs italic leading-relaxed text-muted"
          >
            {citations[open].snippet}
          </motion.blockquote>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-0.5">
      {[0, 0.18, 0.36].map((delay) => (
        <motion.span
          key={delay}
          animate={{ y: [0, -4, 0], opacity: [0.4, 1, 0.4] }}
          transition={{
            duration: 0.9,
            repeat: Infinity,
            ease: "easeInOut",
            delay,
          }}
          className="h-1.5 w-1.5 rounded-full bg-accent"
        />
      ))}
    </div>
  );
}

export default function AskPage() {
  const { toast } = useToast();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingThread, setLoadingThread] = useState(false);

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [topK, setTopK] = useState(5);
  const [selectedDocs, setSelectedDocs] = useState<number[]>([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const loadConversations = useCallback(() => {
    api
      .listConversations()
      .then(setConversations)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    loadConversations();
    api
      .listDocuments()
      .then((docs) =>
        setDocuments(docs.filter((doc) => doc.status === "completed")),
      )
      .catch(() => undefined);
  }, [loadConversations]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [input]);

  const readyDocs = useMemo(
    () => documents.filter((doc) => doc.status === "completed"),
    [documents],
  );

  const activeConversation = useMemo(
    () => conversations.find((item) => item.id === activeId) ?? null,
    [conversations, activeId],
  );

  async function selectConversation(id: number) {
    setDrawerOpen(false);
    if (id === activeId) return;
    setActiveId(id);
    setLoadingThread(true);
    try {
      const detail = await api.getConversation(id);
      setMessages(
        detail.messages.map((message) => ({
          id: String(message.id),
          role: message.role,
          content: message.content,
          citations: message.citations ?? [],
        })),
      );
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Failed to open chat.";
      toast(message, "error");
    } finally {
      setLoadingThread(false);
    }
  }

  function startNewChat() {
    setActiveId(null);
    setMessages([]);
    setDrawerOpen(false);
    setInput("");
    textareaRef.current?.focus();
  }

  async function deleteConversation(id: number, event: React.MouseEvent) {
    event.stopPropagation();
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((item) => item.id !== id));
      if (id === activeId) startNewChat();
      toast("Chat deleted.", "success");
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Failed to delete chat.";
      toast(message, "error");
    }
  }

  async function send(question: string) {
    const trimmed = question.trim();
    if (!trimmed || sending) return;

    const userMessage: ChatMessage = {
      id: createLocalId("user"),
      role: "user",
      content: trimmed,
      citations: [],
    };
    const pendingId = createLocalId("pending");

    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: pendingId, role: "assistant", content: "", citations: [], pending: true },
    ]);
    setInput("");
    setSending(true);

    try {
      const response = await api.chat({
        question: trimmed,
        conversation_id: activeId,
        top_k: topK,
        document_ids: selectedDocs.length ? selectedDocs : undefined,
      });

      setMessages((prev) =>
        prev.map((message) =>
          message.id === pendingId
            ? {
                id: String(response.message_id),
                role: "assistant",
                content: response.answer,
                citations: response.citations,
                grounded: response.grounded,
              }
            : message,
        ),
      );

      if (activeId === null) {
        setActiveId(response.conversation_id);
        const conversation: Conversation = {
          id: response.conversation_id,
          title: titleFromQuestion(trimmed),
          created_at: new Date().toISOString(),
        };
        setConversations((prev) => [conversation, ...prev]);
        loadConversations();
      }
    } catch (error) {
      setMessages((prev) => prev.filter((message) => message.id !== pendingId));
      const message =
        error instanceof ApiError ? error.message : "Could not get an answer.";
      toast(message, "error");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-full">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-line bg-surface/40 lg:flex">
        <div className="p-3">
          <Button variant="subtle" className="w-full" onClick={startNewChat}>
            <Plus className="h-4 w-4" />
            New chat
          </Button>
        </div>
        <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
          {conversations.length === 0 ? (
            <p className="px-3 py-6 text-center text-xs text-muted">
              No chats yet.
            </p>
          ) : (
            conversations.map((conversation) => {
              const active = conversation.id === activeId;
              return (
                <div
                  key={conversation.id}
                  role="button"
                  tabIndex={0}
                  onClick={() => void selectConversation(conversation.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      void selectConversation(conversation.id);
                    }
                  }}
                  className={cn(
                    "group flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                    active
                      ? "bg-white/[0.07] text-ink"
                      : "text-muted hover:bg-white/[0.04] hover:text-ink",
                  )}
                >
                  <MessagesSquare className="h-3.5 w-3.5 shrink-0" />
                  <span className="min-w-0 flex-1 truncate">
                    {conversation.title ?? "Untitled chat"}
                  </span>
                  <button
                    type="button"
                    onClick={(event) =>
                      void deleteConversation(conversation.id, event)
                    }
                    className="rounded p-0.5 text-muted opacity-0 transition-opacity hover:text-danger focus-visible:opacity-100 group-hover:opacity-100"
                    aria-label="Delete chat"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </aside>

      <AnimatePresence>
        {drawerOpen ? (
          <div className="fixed inset-0 z-40 lg:hidden">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setDrawerOpen(false)}
              className="absolute inset-0 bg-black/60"
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 380, damping: 36 }}
              className="absolute inset-y-0 left-0 flex w-72 flex-col border-r border-line bg-elevated"
            >
              <div className="flex items-center justify-between border-b border-line px-3 py-3">
                <span className="text-sm font-medium">Chats</span>
                <IconButton label="Close" onClick={() => setDrawerOpen(false)}>
                  <X className="h-4 w-4" />
                </IconButton>
              </div>
              <div className="p-3">
                <Button
                  variant="subtle"
                  className="w-full"
                  onClick={startNewChat}
                >
                  <Plus className="h-4 w-4" />
                  New chat
                </Button>
              </div>
              <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
                {conversations.map((conversation) => (
                  <button
                    key={conversation.id}
                    type="button"
                    onClick={() => void selectConversation(conversation.id)}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm",
                      conversation.id === activeId
                        ? "bg-white/[0.07] text-ink"
                        : "text-muted",
                    )}
                  >
                    <MessagesSquare className="h-3.5 w-3.5 shrink-0" />
                    <span className="min-w-0 flex-1 truncate">
                      {conversation.title ?? "Untitled chat"}
                    </span>
                  </button>
                ))}
              </div>
            </motion.div>
          </div>
        ) : null}
      </AnimatePresence>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-2 border-b border-line px-3 py-2.5 sm:px-4">
          <IconButton
            label="Chats"
            className="lg:hidden"
            onClick={() => setDrawerOpen(true)}
          >
            <PanelLeft className="h-4 w-4" />
          </IconButton>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink">
              {activeConversation?.title ?? "New chat"}
            </p>
          </div>

          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSettingsOpen((value) => !value)}
            >
              <SlidersHorizontal className="h-4 w-4" />
              <span className="hidden sm:inline">Options</span>
            </Button>
            <AnimatePresence>
              {settingsOpen ? (
                <>
                  <button
                    type="button"
                    aria-hidden
                    tabIndex={-1}
                    onClick={() => setSettingsOpen(false)}
                    className="fixed inset-0 z-10 cursor-default"
                  />
                  <motion.div
                    initial={{ opacity: 0, y: -6, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -6, scale: 0.98 }}
                    transition={{ duration: 0.18 }}
                    className="absolute right-0 z-20 mt-2 w-64 rounded-xl border border-line bg-elevated p-3 shadow-xl"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-muted">
                          Passages to retrieve
                        </span>
                        <span className="text-xs text-ink">{topK}</span>
                      </div>
                      <input
                        type="range"
                        min={1}
                        max={10}
                        value={topK}
                        onChange={(event) =>
                          setTopK(Number(event.target.value))
                        }
                        className="w-full accent-[var(--color-accent)]"
                      />
                    </div>
                    <div className="mt-4 space-y-2">
                      <span className="text-xs font-medium text-muted">
                        Limit to documents
                      </span>
                      {readyDocs.length === 0 ? (
                        <p className="text-xs text-muted/70">
                          No processed documents yet.
                        </p>
                      ) : (
                        <div className="max-h-40 space-y-1 overflow-y-auto">
                          {readyDocs.map((doc) => {
                            const checked = selectedDocs.includes(doc.id);
                            return (
                              <label
                                key={doc.id}
                                className="flex cursor-pointer items-center gap-2 rounded-md px-1.5 py-1 text-xs text-ink hover:bg-white/[0.04]"
                              >
                                <input
                                  type="checkbox"
                                  checked={checked}
                                  onChange={() =>
                                    setSelectedDocs((prev) =>
                                      checked
                                        ? prev.filter((id) => id !== doc.id)
                                        : [...prev, doc.id],
                                    )
                                  }
                                  className="accent-[var(--color-accent)]"
                                />
                                <span className="truncate">
                                  {doc.original_filename}
                                </span>
                              </label>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </motion.div>
                </>
              ) : null}
            </AnimatePresence>
          </div>
        </header>

        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-4 py-6">
            {loadingThread ? (
              <div className="flex justify-center py-16">
                <Spinner className="h-5 w-5 text-muted" />
              </div>
            ) : messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                className="flex flex-col items-center py-14 text-center"
              >
                <LogoMark className="h-11 w-11" />
                <h2 className="mt-4 text-xl font-semibold tracking-tight">
                  Ask your knowledge base
                </h2>
                <p className="mt-1 max-w-md text-sm text-muted">
                  Answers are grounded in your uploaded documents — with
                  citations you can check.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {EXAMPLES.map((example) => (
                    <button
                      key={example}
                      type="button"
                      onClick={() => void send(example)}
                      className="rounded-full border border-line bg-white/[0.03] px-3.5 py-1.5 text-xs text-muted transition-colors hover:border-accent/40 hover:text-ink"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </motion.div>
            ) : (
              <div className="space-y-5">
                {messages.map((message) =>
                  message.role === "user" ? (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex justify-end"
                    >
                      <div className="max-w-[85%] rounded-2xl rounded-br-md bg-accent/15 px-4 py-2.5 text-sm text-ink ring-1 ring-inset ring-accent/20">
                        {message.content}
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-3"
                    >
                      <LogoMark className="mt-0.5 h-7 w-7 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="rounded-2xl rounded-tl-md border border-line bg-surface/70 px-4 py-3 text-sm leading-relaxed text-ink">
                          {message.pending ? (
                            <TypingIndicator />
                          ) : (
                            <p className="whitespace-pre-wrap">
                              {message.content}
                            </p>
                          )}
                        </div>
                        {!message.pending ? (
                          <div className="mt-2 flex items-center gap-2">
                            {message.grounded ? (
                              <Badge tone="accent">
                                <Sparkles className="h-3 w-3" />
                                Grounded
                              </Badge>
                            ) : message.citations.length === 0 ? (
                              <Badge tone="neutral">No sources cited</Badge>
                            ) : null}
                          </div>
                        ) : null}
                        <CitationList citations={message.citations} />
                      </div>
                    </motion.div>
                  ),
                )}
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-line px-3 py-3 sm:px-4">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void send(input);
            }}
            className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-line bg-surface/70 p-2 focus-within:border-accent/50 focus-within:ring-2 focus-within:ring-accent/15"
          >
            <Textarea
              ref={textareaRef}
              value={input}
              rows={1}
              placeholder="Ask a question about your documents…"
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void send(input);
                }
              }}
              className="max-h-44 flex-1 border-none bg-transparent px-2 py-1.5 focus:ring-0"
            />
            <Button
              type="submit"
              variant="primary"
              size="icon"
              disabled={!input.trim() || sending}
              aria-label="Send"
            >
              {sending ? <Spinner /> : <Send className="h-4 w-4" />}
            </Button>
          </form>
          <p className="mx-auto mt-2 max-w-3xl px-1 text-[11px] text-muted/70">
            {selectedDocs.length
              ? `Searching ${selectedDocs.length} selected document${selectedDocs.length === 1 ? "" : "s"}.`
              : "Searching your whole knowledge base."}
            {activeConversation
              ? ` · started ${timeAgo(activeConversation.created_at)}`
              : ""}
          </p>
        </div>
      </section>
    </div>
  );
}

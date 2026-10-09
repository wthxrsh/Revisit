"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  NotebookPen,
  Plus,
  Search,
  StickyNote,
  Trash2,
} from "lucide-react";

import { api, ApiError } from "@/lib/api";
import type { Note } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";
import {
  Button,
  EmptyState,
  Field,
  Input,
  Modal,
  Skeleton,
  Textarea,
} from "@/components/ui";
import { useToast } from "@/components/toast";

export default function NotesPage() {
  const { toast } = useToast();

  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");

  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<Note | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);

  const [pendingDelete, setPendingDelete] = useState<Note | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const handle = setTimeout(() => setDebounced(search.trim()), 280);
    return () => clearTimeout(handle);
  }, [search]);

  const loadNotes = useCallback(() => {
    api
      .listNotes({ search: debounced || undefined })
      .then(setNotes)
      .catch((error) => {
        const message =
          error instanceof ApiError ? error.message : "Failed to load notes.";
        toast(message, "error");
      })
      .finally(() => setLoading(false));
  }, [debounced, toast]);

  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  const countLabel = useMemo(() => {
    if (loading) return "Loading…";
    if (debounced) return `${notes.length} match${notes.length === 1 ? "" : "es"}`;
    return `${notes.length} note${notes.length === 1 ? "" : "s"}`;
  }, [loading, notes.length, debounced]);

  function openCreate() {
    setEditing(null);
    setTitle("");
    setContent("");
    setEditorOpen(true);
  }

  function openEdit(note: Note) {
    setEditing(note);
    setTitle(note.title);
    setContent(note.content);
    setEditorOpen(true);
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim() || !content.trim()) {
      toast("Title and content are required.", "error");
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateNote(editing.id, title.trim(), content);
        setNotes((prev) =>
          prev.map((item) => (item.id === updated.id ? updated : item)),
        );
        toast("Note updated.", "success");
      } else {
        const created = await api.createNote(title.trim(), content);
        setNotes((prev) => [created, ...prev]);
        toast("Note created.", "success");
      }
      setEditorOpen(false);
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Could not save the note.";
      toast(message, "error");
    } finally {
      setSaving(false);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await api.deleteNote(pendingDelete.id);
      setNotes((prev) => prev.filter((item) => item.id !== pendingDelete.id));
      toast("Note deleted.", "success");
      setPendingDelete(null);
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Could not delete the note.";
      toast(message, "error");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
              <NotebookPen className="h-4 w-4 text-accent" />
              Notes
            </h1>
            <p className="mt-0.5 text-xs text-muted">{countLabel}</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative flex-1 sm:w-64 sm:flex-none">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
              <Input
                placeholder="Search notes…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="pl-9"
              />
            </div>
            <Button variant="primary" onClick={openCreate}>
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">New note</span>
            </Button>
          </div>
        </header>

        <div className="mt-6">
          {loading ? (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={index} className="h-32" />
              ))}
            </div>
          ) : notes.length === 0 ? (
            <EmptyState
              icon={<StickyNote className="h-5 w-5" />}
              title={debounced ? "No notes match your search" : "No notes yet"}
              description={
                debounced
                  ? "Try a different keyword."
                  : "Capture a thought, a quote, or something worth revisiting."
              }
              action={
                debounced ? undefined : (
                  <Button variant="primary" onClick={openCreate}>
                    <Plus className="h-4 w-4" />
                    New note
                  </Button>
                )
              }
            />
          ) : (
            <motion.div layout className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <AnimatePresence mode="popLayout">
                {notes.map((note) => (
                  <motion.div
                    key={note.id}
                    layout
                    role="button"
                    tabIndex={0}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.97 }}
                    transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                    whileHover={{ y: -2 }}
                    onClick={() => openEdit(note)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        openEdit(note);
                      }
                    }}
                    className={cn(
                      "group relative flex cursor-pointer flex-col rounded-2xl border border-line bg-surface/70 p-4 text-left outline-none transition-colors",
                      "hover:border-line-strong hover:bg-surface focus-visible:border-accent/60 focus-visible:ring-2 focus-visible:ring-accent/25",
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h2 className="line-clamp-1 text-sm font-medium text-ink">
                        {note.title}
                      </h2>
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          setPendingDelete(note);
                        }}
                        className="rounded-md p-1 text-muted opacity-0 transition-opacity hover:bg-danger/15 hover:text-danger focus-visible:opacity-100 group-hover:opacity-100"
                        aria-label="Delete note"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <p className="mt-2 line-clamp-3 whitespace-pre-wrap text-xs leading-relaxed text-muted">
                      {note.content}
                    </p>
                    <span className="mt-3 text-[11px] text-muted/70">
                      {timeAgo(note.updated_at)}
                    </span>
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </div>
      </div>

      <Modal
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        title={editing ? "Edit note" : "New note"}
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditorOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              loading={saving}
              onClick={handleSave}
              type="submit"
              form="note-form"
            >
              {editing ? "Save changes" : "Create note"}
            </Button>
          </>
        }
      >
        <form id="note-form" onSubmit={handleSave} className="space-y-4">
          <Field label="Title">
            <Input
              autoFocus
              value={title}
              maxLength={255}
              placeholder="Give this note a title"
              onChange={(event) => setTitle(event.target.value)}
            />
          </Field>
          <Field label="Content">
            <Textarea
              value={content}
              rows={9}
              placeholder="Write something worth revisiting…"
              onChange={(event) => setContent(event.target.value)}
            />
          </Field>
        </form>
      </Modal>

      <Modal
        open={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        title="Delete note"
        width="max-w-sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setPendingDelete(null)}>
              Keep it
            </Button>
            <Button variant="danger" loading={deleting} onClick={confirmDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-muted">
          Delete{" "}
          <span className="text-ink">“{pendingDelete?.title}”</span>? This
          can’t be undone.
        </p>
      </Modal>
    </div>
  );
}

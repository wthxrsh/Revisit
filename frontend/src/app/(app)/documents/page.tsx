"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  CloudUpload,
  FileText,
  Files,
  RefreshCw,
  Trash2,
  UploadCloud,
} from "lucide-react";

import { api, ApiError } from "@/lib/api";
import type { Document, DocumentStatus } from "@/lib/types";
import { cn, formatBytes, timeAgo } from "@/lib/utils";
import { Badge, Button, EmptyState, IconButton, Modal, Skeleton } from "@/components/ui";
import { useToast } from "@/components/toast";

const STATUS: Record<
  DocumentStatus,
  { label: string; tone: "neutral" | "accent" | "success" | "warning" | "danger" }
> = {
  pending: { label: "Pending", tone: "neutral" },
  processing: { label: "Processing", tone: "warning" },
  completed: { label: "Ready", tone: "success" },
  failed: { label: "Failed", tone: "danger" },
};

function isBusy(status: DocumentStatus): boolean {
  return status === "pending" || status === "processing";
}

export default function DocumentsPage() {
  const { toast } = useToast();
  const inputRef = useRef<HTMLInputElement>(null);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<string[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Document | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [reprocessing, setReprocessing] = useState<number | null>(null);

  const load = useCallback(
    (silent = false) => {
      api
        .listDocuments()
        .then(setDocuments)
        .catch((error) => {
          const message =
            error instanceof ApiError
              ? error.message
              : "Failed to load documents.";
          toast(message, "error");
        })
        .finally(() => {
          if (!silent) setLoading(false);
        });
    },
    [toast],
  );

  useEffect(() => {
    load();
  }, [load]);

  const hasBusy = useMemo(
    () => documents.some((doc) => isBusy(doc.status)),
    [documents],
  );

  useEffect(() => {
    if (!hasBusy) return;
    const interval = setInterval(() => load(true), 3000);
    return () => clearInterval(interval);
  }, [hasBusy, load]);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const list = Array.from(files);

    for (const file of list) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        toast(`“${file.name}” is not a PDF.`, "error");
        continue;
      }
      if (file.size > 20 * 1024 * 1024) {
        toast(`“${file.name}” exceeds the 20 MB limit.`, "error");
        continue;
      }

      setUploading((prev) => [...prev, file.name]);
      try {
        const created = await api.uploadDocument(file);
        setDocuments((prev) => [
          created,
          ...prev.filter((item) => item.id !== created.id),
        ]);
        toast(
          created.status === "failed"
            ? `“${file.name}” could not be processed.`
            : `“${file.name}” uploaded.`,
          created.status === "failed" ? "error" : "success",
        );
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : `Failed to upload “${file.name}”.`;
        toast(message, "error");
      } finally {
        setUploading((prev) => prev.filter((name) => name !== file.name));
      }
    }
    if (inputRef.current) inputRef.current.value = "";
  }

  async function handleReprocess(doc: Document) {
    setReprocessing(doc.id);
    try {
      const updated = await api.reprocessDocument(doc.id);
      setDocuments((prev) =>
        prev.map((item) => (item.id === updated.id ? updated : item)),
      );
      toast("Document reprocessed.", "success");
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Reprocess failed.";
      toast(message, "error");
    } finally {
      setReprocessing(null);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await api.deleteDocument(pendingDelete.id);
      setDocuments((prev) => prev.filter((item) => item.id !== pendingDelete.id));
      toast("Document deleted.", "success");
      setPendingDelete(null);
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Delete failed.";
      toast(message, "error");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="flex items-center gap-2 text-lg font-semibold tracking-tight">
              <Files className="h-4 w-4 text-accent" />
              Documents
            </h1>
            <p className="mt-0.5 text-xs text-muted">
              {loading
                ? "Loading…"
                : `${documents.length} document${documents.length === 1 ? "" : "s"}`}
            </p>
          </div>
        </header>

        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragActive(false);
            void handleFiles(event.dataTransfer.files);
          }}
          className={cn(
            "mt-6 flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed px-6 py-8 text-center transition-colors",
            dragActive
              ? "border-accent/70 bg-accent/[0.06]"
              : "border-line bg-surface/40",
          )}
        >
          <motion.div
            animate={{ y: dragActive ? -3 : 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 22 }}
            className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/[0.05] text-accent"
          >
            <UploadCloud className="h-5 w-5" />
          </motion.div>
          <p className="text-sm text-ink">
            Drag a PDF here, or{" "}
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="font-medium text-accent underline-offset-4 hover:underline"
            >
              browse
            </button>
          </p>
          <p className="text-xs text-muted">PDF only · up to 20 MB</p>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            multiple
            hidden
            onChange={(event) => void handleFiles(event.target.files)}
          />
        </div>

        <AnimatePresence>
          {uploading.length > 0 ? (
            <motion.ul
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3 space-y-2 overflow-hidden"
            >
              {uploading.map((name) => (
                <li
                  key={name}
                  className="flex items-center gap-3 rounded-xl border border-line bg-surface/60 px-3.5 py-2.5 text-sm"
                >
                  <CloudUpload className="h-4 w-4 animate-pulse text-accent" />
                  <span className="truncate">{name}</span>
                  <span className="ml-auto text-xs text-muted">Uploading…</span>
                </li>
              ))}
            </motion.ul>
          ) : null}
        </AnimatePresence>

        <div className="mt-6">
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} className="h-16" />
              ))}
            </div>
          ) : documents.length === 0 ? (
            <EmptyState
              icon={<FileText className="h-5 w-5" />}
              title="No documents yet"
              description="Upload a PDF to make its contents searchable and ask questions about it."
            />
          ) : (
            <ul className="space-y-2">
              <AnimatePresence initial={false}>
                {documents.map((doc) => {
                  const status = STATUS[doc.status];
                  return (
                    <motion.li
                      key={doc.id}
                      layout
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
                      className="flex items-center gap-3 rounded-2xl border border-line bg-surface/70 px-3.5 py-3"
                    >
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.05] text-muted">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="truncate text-sm font-medium text-ink">
                            {doc.original_filename}
                          </p>
                          <Badge tone={status.tone}>{status.label}</Badge>
                        </div>
                        <p className="mt-0.5 truncate text-xs text-muted">
                          {formatBytes(doc.file_size)}
                          {doc.page_count
                            ? ` · ${doc.page_count} page${doc.page_count === 1 ? "" : "s"}`
                            : ""}
                          {` · ${timeAgo(doc.created_at)}`}
                          {doc.error_message ? ` · ${doc.error_message}` : ""}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <IconButton
                          label="Reprocess"
                          disabled={
                            reprocessing === doc.id || isBusy(doc.status)
                          }
                          onClick={() => void handleReprocess(doc)}
                        >
                          <RefreshCw
                            className={cn(
                              "h-4 w-4",
                              reprocessing === doc.id && "animate-spin",
                            )}
                          />
                        </IconButton>
                        <IconButton
                          label="Delete"
                          className="hover:bg-danger/15 hover:text-danger"
                          onClick={() => setPendingDelete(doc)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </IconButton>
                      </div>
                    </motion.li>
                  );
                })}
              </AnimatePresence>
            </ul>
          )}
        </div>
      </div>

      <Modal
        open={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        title="Delete document"
        width="max-w-sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button variant="danger" loading={deleting} onClick={confirmDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-muted">
          Delete{" "}
          <span className="text-ink">
            “{pendingDelete?.original_filename}”
          </span>
          ? Its chunks and embeddings will be removed too.
        </p>
      </Modal>
    </div>
  );
}

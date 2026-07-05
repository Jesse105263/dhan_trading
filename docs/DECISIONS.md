# Architectural Decisions

Decision 001

Docker manages all infrastructure.

Reason

Portable development.

---

Decision 002

PostgreSQL is the primary database.

Reason

Scalability.

---

Decision 003

Redis stores only real-time data.

Reason

Performance.

---

Decision 004

CSV files are temporary.

Reason

Database-first architecture.

---

Decision 005

LLMs never execute trades.

Reason

Trading must remain deterministic.

---

Decision 006

One milestone per session.

Reason

Maintain documentation quality.

---

Decision 007

Every command must specify:

- Application
- Folder
- Terminal
- Virtual Environment

Reason

Remove ambiguity.

---

Decision 008

No versioned filenames.

Use Git history instead.

Reason

Cleaner project.
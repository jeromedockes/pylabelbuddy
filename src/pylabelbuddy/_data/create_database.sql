CREATE TABLE IF NOT EXISTS document (
  id INTEGER PRIMARY KEY, content TEXT UNIQUE NOT NULL, extra_data TEXT);

CREATE TABLE IF NOT EXISTS label(
  id INTEGER PRIMARY KEY,
  string_form TEXT UNIQUE NOT NULL,
  color TEXT NOT NULL DEFAULT "yellow");

CREATE TABLE IF NOT EXISTS annotation(
  doc_id NOT NULL REFERENCES document (id) ON DELETE CASCADE,
  label_id NOT NULL REFERENCES label(id) ON DELETE CASCADE,
  start_char INTEGER NOT NULL,
  end_char INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS annotation_doc_id_idx ON annotation(doc_id);
CREATE INDEX IF NOT EXISTS annotation_label_id_idx ON annotation(label_id);

CREATE TABLE IF NOT EXISTS app_state (
last_visited_doc INTEGER REFERENCES document (id) ON DELETE SET NULL
);
INSERT INTO app_state (last_visited_doc) SELECT (null)
WHERE NOT EXISTS (SELECT * from app_state);

CREATE TABLE IF NOT EXISTS app_state_extra (
key TEXT UNIQUE NOT NULL, value
);

CREATE VIEW IF NOT EXISTS unlabelled_document AS
SELECT * FROM document
WHERE id NOT IN (SELECT doc_id FROM annotation);

-- slower than the subquery above
-- CREATE VIEW IF NOT EXISTS unlabelled_document AS
-- SELECT document.* FROM document LEFT JOIN annotation
-- ON annotation.doc_id = document.id
-- WHERE annotation.rowid IS NULL;

CREATE VIEW IF NOT EXISTS labelled_document AS
SELECT distinct * FROM document
WHERE id IN (SELECT doc_id FROM annotation);

-- slower than the subquery above
-- create view if not exists labelled_document as
-- select distinct document.* from document
-- inner join annotation
-- on annotation.doc_id = document.id;

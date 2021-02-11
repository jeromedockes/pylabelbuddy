import sqlite3
import tkinter as tk

from pylabelbuddy import _database


class AnnotationsManager(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_doc_id = None
        self.connection = _database.get_connection()
        self.refresh()

    def change_database(self, *args):
        self.connection = _database.get_connection()
        self.current_doc_id = None
        self.refresh()
        self.event_generate("<<VisitedDocChanged>>")

    def refresh(self, *args):
        changed = False
        if self.current_doc_id is not None:
            if not self.connection.execute(
                "select id from document where id = ?", (self.current_doc_id,)
            ).fetchall():
                self.current_doc_id = None
                changed = True
        self.visit_document(self.current_doc_id)
        if changed:
            self.event_generate("<<VisitedDocChanged>>")

    @property
    def labels_info(self):
        labels_info = {}
        for l_id, l_val, l_col in self.connection.execute(
            "SELECT id, string_form, color FROM label order by id"
        ):
            labels_info[l_val] = {"id": l_id, "color": l_col}
        return labels_info

    def visit_document(self, doc_id=None):
        changed = False
        if doc_id is not None:
            exists = self.connection.execute(
                "select count(*) as count from document where id = ?",
                (doc_id,),
            ).fetchone()["count"]
            if not exists:
                doc_id = None
        if doc_id is None:
            try:
                doc_id = self.connection.execute(
                    "select last_visited_doc from app_state"
                ).fetchone()[0]
                doc_id = int(doc_id)
            except Exception:
                doc_id = None
        if doc_id is None:
            doc_id = self.doc_position_to_id(0)
        if doc_id != self.current_doc_id:
            changed = True
        self.current_doc_id = doc_id
        try:
            with self.connection:
                self.connection.execute(
                    "update app_state set last_visited_doc = ?",
                    (self.current_doc_id,),
                )
        except sqlite3.Error:
            self.current_doc_id = None
        if changed:
            self.event_generate("<<VisitedDocChanged>>")

    def visit_next(self, *args):
        next_doc = self.connection.execute(
            "select min(id) from document where id > ? ",
            (self.current_doc_id,),
        ).fetchone()
        if next_doc is None:
            return
        self.visit_document(next_doc[0])

    def visit_prev(self, *args):
        prev_doc = self.connection.execute(
            "select max(id) from document where id < ? ",
            (self.current_doc_id,),
        ).fetchone()
        if prev_doc is None:
            return
        self.visit_document(prev_doc[0])

    def visit_next_labelled(self, *args):
        next_labelled = self.connection.execute(
            "select min(doc_id) from annotation where doc_id > ? ",
            (self.current_doc_id,),
        ).fetchone()
        if next_labelled is None:
            return
        self.visit_document(next_labelled[0])

    def visit_prev_labelled(self, *args):
        prev_labelled = self.connection.execute(
            "select max(doc_id) from annotation where doc_id < ? ",
            (self.current_doc_id,),
        ).fetchone()
        if prev_labelled is None:
            return
        self.visit_document(prev_labelled[0])

    def visit_next_unlabelled(self, *args):
        next_unlabelled = self.connection.execute(
            "select id from unlabelled_document where id > ? "
            "order by id limit 1",
            (self.current_doc_id,),
        ).fetchone()
        if next_unlabelled is None:
            return
        self.visit_document(next_unlabelled[0])

    def visit_prev_unlabelled(self, *args):
        prev_unlabelled = self.connection.execute(
            "select id from unlabelled_document "
            "where id < ? order by id desc limit 1",
            (self.current_doc_id,),
        ).fetchone()
        if prev_unlabelled is None:
            return
        self.visit_document(prev_unlabelled[0])

    def n_docs(self):
        return self.connection.execute(
            "select count(*) from document"
        ).fetchone()[0]

    def current_doc_position(self):
        return self.connection.execute(
            "select count(*) from document where id < ?",
            (self.current_doc_id,),
        ).fetchone()[0]

    def doc_position_to_id(self, position):
        try:
            return self.connection.execute(
                "select id from document order by id limit 1 offset ?",
                (position,),
            ).fetchone()[0]
        except Exception:
            return None

    @property
    def label_colors(self):
        return {k: v["color"] for (k, v) in self.labels_info.items()}

    @property
    def content(self):
        try:
            cur = self.connection.execute(
                "select content from document where id=:docid",
                dict(docid=self.current_doc_id),
            )
            return cur.fetchone()[0]
        except Exception:
            return None

    def existing_regions(self):
        results = self.connection.execute(
            "select annotation.rowid, label.string_form, start_char, "
            "end_char from annotation inner join label on "
            "annotation.label_id = label.id where annotation.doc_id = ?",
            (self.current_doc_id,),
        )
        yield from results

    def add_annotation(self, label, start_char, end_char):
        n_annotations_before = self.connection.execute(
            "select count(*) from annotation where doc_id = ?",
            (self.current_doc_id,),
        ).fetchone()[0]
        statement = (
            "insert into annotation (doc_id, label_id, "
            "start_char, end_char) values (?, ?, ?, ?)"
        )
        labels_info = self.labels_info
        if label not in labels_info:
            return None
        label_id = labels_info[label]["id"]
        try:
            with self.connection:
                cur = self.connection.execute(
                    statement,
                    (self.current_doc_id, label_id, start_char, end_char),
                )
            if n_annotations_before == 0:
                self.event_generate("<<DocumentStatusChanged>>")
            return cur.lastrowid
        except sqlite3.Error:
            return None

    def delete_annotation(self, annotation_id):
        annotation_id = int(annotation_id)
        n_annotations_before = self.connection.execute(
            "select count(*) from annotation where "
            "doc_id in (select doc_id from annotation where rowid = ?)",
            (annotation_id,),
        ).fetchone()[0]
        try:
            with self.connection:
                self.connection.execute(
                    "delete from annotation where rowid = ?",
                    (annotation_id,),
                )
        except sqlite3.Error:
            pass
        if n_annotations_before == 1:
            self.event_generate("<<DocumentStatusChanged>>")

    def update_annotation_label(self, annotation_id, new_label):
        annotation_id = int(annotation_id)
        labels_info = self.labels_info
        if new_label not in labels_info:
            return
        label_id = labels_info[new_label]["id"]
        try:
            with self.connection:
                self.connection.execute(
                    "update annotation set label_id = ? where rowid = ?",
                    (label_id, annotation_id),
                )
        except sqlite3.Error:
            pass

    def first_doc(self):
        res = self.connection.execute(
            "select id from document order by id limit 1"
        ).fetchone()
        if res is None:
            return None
        return res[0]

    def last_doc(self):
        res = self.connection.execute(
            "select id from document order by id desc limit 1"
        ).fetchone()
        if res is None:
            return None
        return res[0]

    def first_unlabelled(self):
        res = self.connection.execute(
            "select id from unlabelled_document " "order by id limit 1"
        ).fetchone()
        if res is None:
            return None
        return res[0]

    def last_unlabelled(self):
        res = self.connection.execute(
            "select id from unlabelled_document order by id desc limit 1"
        ).fetchone()
        if res is None:
            return None
        return res[0]

    def first_labelled(self):
        return self.connection.execute(
            "select min(doc_id) from annotation"
        ).fetchone()[0]

    def last_labelled(self):
        return self.connection.execute(
            "select max(doc_id) from annotation"
        ).fetchone()[0]

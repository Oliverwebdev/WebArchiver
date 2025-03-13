import sqlite3
from typing import Dict, List, Any, Optional, Union, Tuple


class DatabaseManager:
    """
    Manages database operations for archived websites.
    
    This class handles all database interactions including initialization,
    CRUD operations for websites, tags, and notes, and query operations.
    """
    
    def __init__(self, db_path: str = "websites.db") -> None:
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to "websites.db".
        """
        self.db_path: str = db_path
        self._init_db()
        
    def _init_db(self) -> None:
        """
        Initialize the database schema if it doesn't exist.
        
        Creates tables for websites, tags, website_tags relations, and notes.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create websites table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS websites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            domain TEXT,
            timestamp TEXT,
            date_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            directory TEXT UNIQUE,
            thumbnail TEXT,
            is_edited BOOLEAN DEFAULT 0,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES websites (id)
        )
        ''')
        
        # Create tags table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        ''')
        
        # Create relation website_tags
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS website_tags (
            website_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (website_id, tag_id),
            FOREIGN KEY (website_id) REFERENCES websites (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        )
        ''')

        # Create notes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_id INTEGER,
            note TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (website_id) REFERENCES websites (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_website(self, metadata: Dict[str, Any]) -> Optional[int]:
        """
        Add a new website to the database.
        
        Args:
            metadata: Dictionary containing website metadata including:
                     url, title, domain, timestamp, directory, thumbnail,
                     is_edited, and parent_id.
        
        Returns:
            The newly created website ID or None if there was an integrity error
            (e.g., directory already exists).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO websites 
            (url, title, domain, timestamp, directory, thumbnail, is_edited, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata.get('url', ''),
                metadata.get('title', 'Unknown Title'),
                metadata.get('domain', ''),
                metadata.get('timestamp', ''),
                metadata.get('directory', ''),
                metadata.get('thumbnail', ''),
                metadata.get('is_edited', False),
                metadata.get('parent_id', None)
            ))
            website_id = cursor.lastrowid
            conn.commit()
            return website_id
        except sqlite3.IntegrityError:
            # Directory already in DB
            return None
        finally:
            conn.close()
    
    def update_website(self, website_id: int, updates: Dict[str, Any]) -> None:
        """
        Update website properties.
        
        Args:
            website_id: ID of the website to update.
            updates: Dictionary of field names and values to update.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(website_id)
        query = f"UPDATE websites SET {set_clause} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
    
    def get_website_by_directory(self, directory: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a website by its directory path.
        
        Args:
            directory: The directory path of the website.
            
        Returns:
            Dict containing website data or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, url, title, domain, timestamp, date_saved, directory, thumbnail, is_edited, parent_id
        FROM websites
        WHERE directory = ?
        ''', (directory,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'domain': row[3],
                'timestamp': row[4],
                'date_saved': row[5],
                'directory': row[6],
                'thumbnail': row[7],
                'is_edited': bool(row[8]),
                'parent_id': row[9]
            }
        return None
    
    def get_all_websites(
        self, 
        search_term: Optional[str] = None, 
        tag: Optional[str] = None, 
        order_by: str = "date_saved DESC"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all websites, optionally filtered by search term or tag.
        
        Args:
            search_term: Optional search term to filter results.
            tag: Optional tag name to filter results.
            order_by: SQL ORDER BY clause for result ordering. Defaults to most recent first.
            
        Returns:
            List of dictionaries containing website data.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
        SELECT id, url, title, domain, timestamp, date_saved, directory, thumbnail, is_edited, parent_id
        FROM websites
        '''
        
        params: List[Any] = []
        where_clauses: List[str] = []
        
        if search_term:
            where_clauses.append("(title LIKE ? OR url LIKE ? OR domain LIKE ?)")
            pattern = f"%{search_term}%"
            params.extend([pattern, pattern, pattern])
        
        if tag:
            query = '''
            SELECT w.id, w.url, w.title, w.domain, w.timestamp, w.date_saved, 
                   w.directory, w.thumbnail, w.is_edited, w.parent_id
            FROM websites w
            JOIN website_tags wt ON w.id = wt.website_id
            JOIN tags t ON wt.tag_id = t.id
            '''
            where_clauses.append("t.name = ?")
            params.append(tag)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += f" ORDER BY {order_by}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results: List[Dict[str, Any]] = []
        for row in rows:
            results.append(dict(row))
        return results
    
    def delete_website(self, website_id: int) -> None:
        """
        Delete a website and its associated tags and notes from the database.
        
        Args:
            website_id: ID of the website to delete.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM website_tags WHERE website_id = ?", (website_id,))
        cursor.execute("DELETE FROM notes WHERE website_id = ?", (website_id,))
        cursor.execute("DELETE FROM websites WHERE id = ?", (website_id,))
        conn.commit()
        conn.close()
    
    def add_tag(self, name: str) -> int:
        """
        Add a tag to the database if it doesn't exist.
        
        Args:
            name: Name of the tag.
            
        Returns:
            ID of the tag (either existing or newly created).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            tag_id = row[0]
        else:
            cursor.execute("INSERT INTO tags (name) VALUES (?)", (name,))
            tag_id = cursor.lastrowid
            conn.commit()
        conn.close()
        return tag_id
    
    def add_website_tag(self, website_id: int, tag_name: str) -> bool:
        """
        Associate a tag with a website.
        
        Args:
            website_id: ID of the website.
            tag_name: Name of the tag to add.
            
        Returns:
            True if successful, False if the association already exists.
        """
        tag_id = self.add_tag(tag_name)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO website_tags (website_id, tag_id)
            VALUES (?, ?)
            ''', (website_id, tag_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_website_tags(self, website_id: int) -> List[Dict[str, Any]]:
        """
        Get all tags associated with a website.
        
        Args:
            website_id: ID of the website.
            
        Returns:
            List of dictionaries containing tag information.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT t.id, t.name
        FROM tags t
        JOIN website_tags wt ON t.id = wt.tag_id
        WHERE wt.website_id = ?
        ORDER BY t.name
        ''', (website_id,))
        rows = cursor.fetchall()
        conn.close()
        tags = [{'id': r[0], 'name': r[1]} for r in rows]
        return tags
    
    def remove_website_tag(self, website_id: int, tag_id: int) -> None:
        """
        Remove a tag association from a website.
        
        Args:
            website_id: ID of the website.
            tag_id: ID of the tag to remove.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        DELETE FROM website_tags
        WHERE website_id = ? AND tag_id = ?
        ''', (website_id, tag_id))
        conn.commit()
        conn.close()
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags with usage counts.
        
        Returns:
            List of dictionaries containing tag information and usage counts.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT t.id, t.name, COUNT(wt.website_id) as count
        FROM tags t
        LEFT JOIN website_tags wt ON t.id = wt.tag_id
        GROUP BY t.id
        ORDER BY count DESC, name
        ''')
        rows = cursor.fetchall()
        conn.close()
        tags = []
        for r in rows:
            tags.append({"id": r[0], "name": r[1], "count": r[2]})
        return tags
    
    def add_note(self, website_id: int, note_text: str) -> int:
        """
        Add a note to a website.
        
        Args:
            website_id: ID of the website.
            note_text: Content of the note.
            
        Returns:
            ID of the newly created note.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO notes (website_id, note)
        VALUES (?, ?)
        ''', (website_id, note_text))
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return note_id
    
    def get_website_notes(self, website_id: int) -> List[Dict[str, Any]]:
        """
        Get all notes for a website.
        
        Args:
            website_id: ID of the website.
            
        Returns:
            List of dictionaries containing note information.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, note, date_created
        FROM notes
        WHERE website_id = ?
        ORDER BY date_created DESC
        ''', (website_id,))
        rows = cursor.fetchall()
        conn.close()
        notes = []
        for r in rows:
            notes.append({"id": r[0], "note": r[1], "date_created": r[2]})
        return notes
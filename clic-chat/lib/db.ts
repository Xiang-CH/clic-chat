import * as lancedb from "@lancedb/lancedb";


export default class DB {
    db: lancedb.Connection | null;
    constructor() {
        this.db = null;
    }

    async connect() {
        this.db = await lancedb.connect("@/../../db");
    }
    async search(query: string, table: string) {
        if (!query)
            return [];
        if (!this.db)
            await this.connect();
            if (!this.db)
                throw new Error("Unable to connect to the database.");

        const tbl = await this.db.openTable(table);
        return await tbl.search(query, "fts").select(["text"]).limit(10).toArray();
    }
}
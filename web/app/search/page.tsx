import { Suspense } from "react";
import SearchClient from "./SearchClient";

export default function Page() {
    return (
        <Suspense fallback={<div className="p-6">Cargando...</div>}>
            <SearchClient />
        </Suspense>
    );
}
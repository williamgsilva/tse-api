import { Link, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { AnalysisPage } from "./pages/AnalysisPage";
import { BallotPage } from "./pages/BallotPage";
import { ExplorePage } from "./pages/ExplorePage";
import { OpenDataPage } from "./pages/OpenDataPage";
import { ResultsPage } from "./pages/ResultsPage";
import { SectionsPage } from "./pages/SectionsPage";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ExplorePage />} />
        <Route path="resultados" element={<ResultsPage />} />
        <Route path="secoes" element={<SectionsPage />} />
        <Route path="secoes/:pleito/:uf/:municipio/:zona/:secao" element={<BallotPage />} />
        <Route path="analises" element={<AnalysisPage />} />
        <Route path="dados-abertos" element={<OpenDataPage />} />
        <Route
          path="*"
          element={
            <div className="page__header">
              <h1>Página não encontrada</h1>
              <Link to="/">Voltar para o mapa</Link>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}

export default function Carregando() {
  return (
    <main aria-busy="true">
      <p className="apoio">Carregando.</p>
      <section className="grade-widgets" aria-label="Carregando indicadores">
        {[0, 1].map((indice) => (
          <article className="cartao" key={indice}>
            <div className="esqueleto" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

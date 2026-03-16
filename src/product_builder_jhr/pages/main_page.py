import streamlit as st
from product_builder_jhr.models.tax import TaxResult
from product_builder_jhr.services.tax import calculate_net_from_ral
from product_builder_jhr.config.config import config_class as _default_config
from functools import cache
from decimal import Decimal
import plotly.graph_objects as go

def _show_sankey(t: TaxResult):
    # msg - x coord - y coord - color - value
    nodi_config = {
    "ral":(f"RAL: {t.ral:.0f}€", 0.0, 0.4,"#2c3e50", t.ral),
    "cuneo":(f"Cuneo fiscale: {t.cuneo:.0f}€", 0.0, 0.0, "#2ecc71", t.cuneo),
    "inps":(f"Contributi INPS: {t.contributo_inps:.0f}€", 0.25, 0.9, "#FF0000", t.contributo_inps),
    "imponibile":(f"Imponibile fiscale: {t.imponibile_fiscale:.0f}€", 0.25, 0.4,  "#e67e22", t.imponibile_fiscale),
    "irpef":(f"IRPEF: {t.irpef:.0f}€", 0.55, 0.7,"#e67e22", t.irpef),      # 4: Sotto imponibile
    "addizionale_comunale":(f"Addizionale comunale: {t.addizionale_comunale:.0f}€", 0.57, 0.9,"#e67e22", t.addizionale_comunale),
    "addizionale_regionale":(f"Addizionale regionale: {t.addizionale_regionale:.0f}€", 0.59, 0.98,"#e67e22", t.addizionale_regionale),
    "imposta_lorda":(f"Imposta Lorda: {t.imposta_lorda:.0f}€", 0.70, 0.85,  "#e67e22",t.imposta_lorda),
    "detrazioni":(f"Detrazioni lavoro dipendente : {t.detrazioni:.0f}€", 0.75, 0.6,  "#2ecc71", t.detrazioni),
    "imposta_netta":(f"Imposta netta: {t.imposta_netta:.0f}€", 0.85, 0.95,  "#FF0000", t.imposta_netta),
    "netto":(f"Netto annuale: {t.netto:.0f}€", 0.85, 0.2, "#2ecc71", t.netto),
    "netto_mensile":(f"Netto mensile: {t.netto_mensile:.0f}€", 0.95, 0.5, "#2ecc71", t.netto_mensile)
}

    active_nodes = {k: v for k, v in nodi_config.items() if v[-1] > 0}
    node_index = {k: i for i, k in enumerate(active_nodes)}  # name → index lookup

    labels_list = [v[0] for v in active_nodes.values()]
    x_coords    = [v[1] for v in active_nodes.values()]
    y_coords    = [v[2] for v in active_nodes.values()]
    colors      = [v[3] for v in active_nodes.values()]
    @cache
    def idx(name: str) -> int | None:
        return node_index.get(name)

    flussi_potenziali = [
        (idx("ral"),                  idx("inps"),                 t.contributo_inps),
        (idx("ral"),                  idx("imponibile"),           t.imponibile_fiscale - t.cuneo),
        (idx("cuneo"),                idx("imponibile"),           t.cuneo),
        (idx("imponibile"),           idx("irpef"),                t.irpef),
        (idx("imponibile"),           idx("addizionale_comunale"), t.addizionale_comunale),
        (idx("imponibile"),           idx("addizionale_regionale"),t.addizionale_regionale),
        (idx("irpef"),                idx("imposta_lorda"),        t.irpef - t.detrazioni),
        (idx("irpef"),                idx("detrazioni"),        t.detrazioni),
        (idx("addizionale_comunale"), idx("imposta_lorda"),        t.addizionale_comunale),
        (idx("addizionale_regionale"),idx("imposta_lorda"),        t.addizionale_regionale),
        #(idx("imposta_lorda"),        idx("detrazioni"),           t.detrazioni),
        (idx("imposta_lorda"),        idx("imposta_netta"),        t.imposta_netta),
        (idx("detrazioni"),           idx("netto"),                t.detrazioni),
        (idx("imponibile"),           idx("netto"),                t.netto - t.detrazioni),
        (idx("netto"),                idx("netto_mensile"),               t.netto_mensile),
    ]
    flussi_attivi = [
        f for f in flussi_potenziali
        if f[2] > 0.01 and f[0] is not None and f[1] is not None 
    ]
    source = [f[0] for f in flussi_attivi]
    target = [f[1] for f in flussi_attivi]
    value  = [f[2] for f in flussi_attivi]
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=15,
            line=dict(color="black", width=0.5),
            label=labels_list,
            x=x_coords,
            y=y_coords,
            color=colors,
        ),
        valueformat=".0f",
        valuesuffix="€", 
        link=dict(
            source=source,
            target=target,
            value=value,
            color="rgba(180,180,180,0.4)",
        ),
    )])

    fig.update_layout(
        title_text=f"Analisi fiscale RAL {t.ral:.0f}€: Dal lordo al netto",
        font_size=12,
        width=1600,
        height=900,
        hoverlabel=dict(
            font_size=12,
            font_color="white",
            bgcolor="black",
        ),
    )

    st.plotly_chart(fig, width='content')
def show_main_page():
    ral = st.text_input("RAL", key="ral", value='35000')
    selectbox_mesi = st.selectbox("Mesi", [12,13,14], index=0, placeholder="Scegli il numero di mensilità...")
    selectbox_regione = st.selectbox(
        'Regione di residenza',
        (_default_config.addizionali_regionali.index.drop_duplicates()), index=None, placeholder="Scegli la regione di residenza..."
    )
    comuni = _default_config.addizionali_comunali[_default_config.addizionali_comunali['Denominazione Regione'] == selectbox_regione]['COMUNE']
    selectbox_comune = st.selectbox(
        'Comune di residenza',
        comuni, placeholder = 'Scegli il comune di residenza...', index=None, disabled=False if selectbox_regione else True
    )

    submitted = st.button("Calcola", disabled=False if selectbox_regione and selectbox_comune else True)
    if submitted:    
        tax_result = calculate_net_from_ral(Decimal(ral), selectbox_comune, selectbox_regione, selectbox_mesi)
        st.metric(label="Netto Annuale", value=f"€ {tax_result.netto:,.0f}")
        _show_sankey(tax_result)

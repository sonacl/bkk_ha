class BKKStopCard extends HTMLElement {
  set hass(hass) {
    if (!this.content) {
      const card = document.createElement('ha-card');
      const container = document.createElement('div');
      container.id = 'container';
      const style = document.createElement('style');
      style.textContent = `
        #container { padding: 0 16px 16px 16px; }
        #station-header { 
          padding: 16px; 
          font-weight: bold; 
          font-size: 1.2em; 
          display: flex; 
          justify-content: space-between; 
          align-items: center; 
        }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 8px 0; }
        .vehicle-box { 
          font-weight: bold; 
          font-size: 1.1em; 
          width: 50px; 
          height: 30px;
          line-height: 30px;
          text-align: center; 
          border-radius: 4px; 
          color: white;
          display: inline-block;
        }
        .headsign { padding-left: 12px; font-weight: 500; }
        .arrival { text-align: right; font-weight: bold; font-size: 1.1em; min-width: 60px; }
        .estimated { color: #208C4E; }
        .refresh-icon { cursor: pointer; color: var(--secondary-text-color); }
        
        /* Vehicle Colors */
        .bus_bg { background-color: #009FE3; }
        .bus_night_bg { background-color: #000000; }
        .trolleybus_bg { background-color: #E5231B; }
        .tram_bg { background-color: #FFD500; color: black !important; }
        .rail_bg { background-color: #2ECC71; }
        .subway_bg { background-color: #E5231B; }
      `;
      card.appendChild(style);
      
      const header = document.createElement('div');
      header.id = 'station-header';
      header.innerHTML = `<span id="name"></span><ha-icon icon="mdi:sync" class="refresh-icon" id="refresh-icon"></ha-icon>`;
      card.appendChild(header);
      card.appendChild(container);
      this.appendChild(card);
      
      this.content = container;
      this.headerName = this.querySelector('#name');
      this.querySelector('#refresh-icon').addEventListener('click', () => {
        hass.callService('homeassistant', 'update_entity', { entity_id: this.config.entity });
      });
    }

    const entityId = this.config.entity;
    const state = hass.states[entityId];

    if (!state) {
      this.content.innerHTML = "Entity not found: " + entityId;
      return;
    }

    const attrs = state.attributes;
    this.headerName.innerText = this.config.name || attrs.stationName || "BKK Stop";

    let html = "<table>";
    if (attrs.vehicles && attrs.vehicles.length > 0) {
      attrs.vehicles.forEach(v => {
        let vClass = v.type.toLowerCase();
        // Night bus check
        if (vClass === "bus" && /^(6|9[0-9]{2}[A-Z]?)$/.test(v.routeid)) {
          vClass += "_night";
        }
        
        const isEstimated = v.predicted_attime ? 'estimated' : '';
        const displayTime = v.in === "0" ? "now" : v.in + "'";

        html += `
          <tr>
            <td style="width: 50px;"><div class="vehicle-box ${vClass}_bg">${v.routeid}</div></td>
            <td class="headsign">${v.headsign}</td>
            <td class="arrival ${isEstimated}">${displayTime}</td>
          </tr>
        `;
      });
    } else {
      html += "<tr><td colspan='3' style='text-align: center; padding: 20px;'>No departures scheduled</td></tr>";
    }
    html += "</table>";
    this.content.innerHTML = html;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity');
    }
    this.config = config;
  }

  getCardSize() {
    return this.config.entities ? this.config.entities.length : 3;
  }
}

customElements.define('bkk-stop-card', BKKStopCard);

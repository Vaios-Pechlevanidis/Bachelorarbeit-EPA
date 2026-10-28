// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export const waitForElementReady = async (element, timeout = 5000) => {
    if (!element) {
        console.warn('waitForElementReady: Element ist null');
        return false;
    }

    const startTime = Date.now();
    
    return new Promise((resolve) => {
        const checkReady = () => {
            if (Date.now() - startTime > timeout) {
                console.warn('waitForElementReady: Timeout erreicht');
                resolve(false);
                return;
            }

            const hasSize = element.offsetWidth > 0 && element.offsetHeight > 0;
            const isVisible = element.offsetParent !== null;
            const hasContent = element.children.length > 0;

            if (hasSize && isVisible && hasContent) {
                console.log('✅ Element ist bereit:', element.id);
                resolve(true);
            } else {
                setTimeout(checkReady, 50);
            }
        };

        checkReady();
    });
};

export const validateChart = (element, name = 'Chart') => {
    const result = {
        isValid: false,
        message: '',
        details: {}
    };

    if (!element) {
        result.message = `${name} Element nicht gefunden`;
        return result;
    }

    const width = element.offsetWidth;
    const height = element.offsetHeight;
    
    result.details.width = width;
    result.details.height = height;

    if (width === 0 || height === 0) {
        result.message = `${name} hat keine Größe (${width}x${height})`;
        return result;
    }

    if (element.offsetParent === null) {
        result.message = `${name} ist nicht sichtbar (display: none oder visibility: hidden)`;
        return result;
    }

    const svg = element.querySelector('svg');
    if (!svg) {
        result.message = `${name} hat kein SVG-Element`;
        return result;
    }

    result.details.svgWidth = svg.getAttribute('width') || svg.clientWidth;
    result.details.svgHeight = svg.getAttribute('height') || svg.clientHeight;

    const paths = svg.querySelectorAll('path, line, rect, circle, text');
    result.details.elementCount = paths.length;

    if (paths.length === 0) {
        result.message = `${name} SVG ist leer (keine Pfade/Shapes gefunden)`;
        return result;
    }

    const rechartsElements = svg.querySelectorAll('[class*="recharts"]');
    result.details.rechartsElementCount = rechartsElements.length;

    if (rechartsElements.length === 0) {
        result.message = `${name} enthält keine Recharts-Elemente`;
        return result;
    }

    const dataElements = svg.querySelectorAll('.recharts-line, .recharts-area, .recharts-bar, .recharts-pie');
    result.details.dataElementCount = dataElements.length;

    if (dataElements.length === 0) {
        console.warn(`${name}: Keine Daten-Visualisierungselemente gefunden, könnte leer sein`);
    }

    result.isValid = true;
    result.message = `${name} ist vollständig und bereit`;
    
    return result;
};

export const waitForChartReady = async (chartId, maxWaitTime = 10000) => {
    console.log(`⏳ Warte auf Chart: ${chartId}`);
    
    const startTime = Date.now();
    const checkInterval = 200;

    return new Promise((resolve) => {
        const checkChart = () => {
            const elapsed = Date.now() - startTime;

            if (elapsed > maxWaitTime) {
                console.error(`❌ Timeout für Chart: ${chartId} nach ${elapsed}ms`);
                resolve({
                    success: false,
                    message: `Timeout nach ${elapsed}ms`,
                    element: null
                });
                return;
            }

            const element = document.getElementById(chartId);
            if (!element) {
                setTimeout(checkChart, checkInterval);
                return;
            }

            const validation = validateChart(element, chartId);

            if (validation.isValid) {
                console.log(`✅ Chart bereit: ${chartId} nach ${elapsed}ms`);
                console.log('Details:', validation.details);
                resolve({
                    success: true,
                    message: validation.message,
                    element: element
                });
            } else {
                setTimeout(checkChart, checkInterval);
            }
        };

        checkChart();
    });
};

export const waitForMultipleCharts = async (chartIds, maxWaitTime = 15000) => {
    console.log(`⏳ Warte auf ${chartIds.length} Charts...`);
    
    const promises = chartIds.map(id => waitForChartReady(id, maxWaitTime));
    const results = await Promise.all(promises);
    
    const allReady = results.every(r => r.success);
    
    if (allReady) {
        console.log(`✅ Alle ${chartIds.length} Charts sind bereit`);
    } else {
        const failed = results.filter(r => !r.success).map(r => r.element?.id || 'unknown');
        console.error(`❌ Einige Charts sind nicht bereit:`, failed);
    }
    
    return {
        allReady,
        results
    };
};

export const waitForImagesInElement = async (element, timeout = 5000) => {
    if (!element) return true;

    const images = element.querySelectorAll('img');
    if (images.length === 0) {
        console.log('Keine Bilder im Element gefunden');
        return true;
    }

    console.log(`⏳ Warte auf ${images.length} Bilder...`);

    const imagePromises = Array.from(images).map(img => {
        if (img.complete && img.naturalHeight !== 0) {
            return Promise.resolve();
        }

        return new Promise((resolve) => {
            const timeoutId = setTimeout(() => {
                console.warn('Bild Timeout:', img.src);
                resolve();
            }, timeout);

            img.onload = () => {
                clearTimeout(timeoutId);
                resolve();
            };

            img.onerror = () => {
                console.error('Bild Ladefehler:', img.src);
                clearTimeout(timeoutId);
                resolve();
            };
        });
    });

    await Promise.all(imagePromises);
    console.log(`✅ Alle ${images.length} Bilder geladen`);
    return true;
};

import { HttpsProxyAgent } from "https-proxy-agent";
import https from "https";
import http from "http";

export function setupProxy(proxyUrl: string): void {
  const proxyAgent = new HttpsProxyAgent(proxyUrl);

  const origHttpsRequest = https.request.bind(https);
  (https as any).request = function (
    url: string | URL | { hostname?: string; path?: string; agent?: any; [key: string]: any },
    options?: any,
    callback?: any
  ) {
    if (options && typeof options === "object") {
      options = { ...options, agent: proxyAgent };
    }
    if (typeof url === "object" && url !== null && !(url instanceof URL) && typeof url !== "string") {
      url = { ...url, agent: proxyAgent };
    }
    return origHttpsRequest(url as any, options, callback);
  };

  const origHttpRequest = http.request.bind(http);
  (http as any).request = function (
    url: string | URL | { hostname?: string; path?: string; agent?: any; [key: string]: any },
    options?: any,
    callback?: any
  ) {
    if (options && typeof options === "object") {
      options = { ...options, agent: proxyAgent };
    }
    if (typeof url === "object" && url !== null && !(url instanceof URL) && typeof url !== "string") {
      url = { ...url, agent: proxyAgent };
    }
    return origHttpRequest(url as any, options, callback);
  };
}

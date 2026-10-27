// See all configuration options: https://remotion.dev/docs/config
// Each option also is available as a CLI flag: https://remotion.dev/docs/cli

// Note: When using the Node.JS APIs, the config file doesn't apply. Instead, pass options directly to the APIs

import { Config } from "@remotion/cli/config";
import { existsSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

Config.setRspack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);

// En la nube, remotion.media está bloqueado: usamos el Chrome Headless Shell
// que instala HyperFrames (scripts/setup.sh). Fuera de la nube, Remotion usa el suyo.
const hfChrome = join(homedir(), ".cache/hyperframes/chrome/chrome-headless-shell");
if (existsSync(hfChrome)) {
  const version = readdirSync(hfChrome).sort().pop();
  if (version) {
    Config.setBrowserExecutable(
      join(hfChrome, version, "chrome-headless-shell-linux64/chrome-headless-shell"),
    );
  }
}

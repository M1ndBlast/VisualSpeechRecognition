import { Console } from "console";

class mConsole extends Console {
	constructor(prefix) {
		super({
			stdout: process.stdout,
			stderr: process.stderr,
			colorMode: true,
		});
		let logger = this;
		logger.log = (...args) => {
			args.unshift(prefix);
			Console.prototype.log.apply(logger, args);
		};
		logger.info = (...args) => {
			args.unshift(prefix);
			Console.prototype.info.apply(logger, args);
		}
		logger.warn = (...args) => {
			args.unshift(prefix);
			Console.prototype.warn.apply(logger, args);
		}
		logger.error = (...args) => {
			args.unshift(prefix);
			Console.prototype.error.apply(logger, args);
		}
		logger.debug = (...args) => {
			args.unshift(prefix);
			Console.prototype.debug.apply(logger, args);
		}
	}
}

export default mConsole;
"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.JigsawPuzzle = void 0;
var react_1 = __importStar(require("react"));
var clamp = function (value, min, max) {
    if (value < min) {
        return min;
    }
    if (value > max) {
        return max;
    }
    return value;
};
var solveTolerancePercentage = 0.028;
var JigsawPuzzle = function (_a) {
    var imageSrc = _a.imageSrc, _b = _a.rows, rows = _b === void 0 ? 3 : _b, _c = _a.columns, columns = _c === void 0 ? 4 : _c, _d = _a.onSolved, onSolved = _d === void 0 ? function () { } : _d;
    if (!imageSrc) {
        return null;
    }
    var _e = (0, react_1.useState)(), tiles = _e[0], setTiles = _e[1];
    var _f = (0, react_1.useState)(), imageSize = _f[0], setImageSize = _f[1];
    var _g = (0, react_1.useState)(), rootSize = _g[0], setRootSize = _g[1];
    var _h = (0, react_1.useState)(), calculatedHeight = _h[0], setCalculatedHeight = _h[1];
    var rootElement = (0, react_1.useRef)();
    var resizeObserver = (0, react_1.useRef)();
    var draggingTile = (0, react_1.useRef)();
    var onImageLoaded = (0, react_1.useCallback)(function (image) {
        setImageSize({ width: image.width, height: image.height });
        if (rootSize) {
            setCalculatedHeight(rootSize.width / image.width * image.height);
        }
        setTiles(Array.from(Array(rows * columns).keys())
            .map(function (position) { return ({
            correctPosition: position,
            tileHeight: image.height / rows,
            tileWidth: image.width / columns,
            tileOffsetX: (position % columns) * (image.width / columns),
            tileOffsetY: Math.floor(position / columns) * (image.height / rows),
            currentPosXPerc: Math.random() * (1 - 1 / rows),
            currentPosYPerc: Math.random() * (1 - 1 / columns),
            solved: false
        }); }));
    }, [rows, columns]);
    var onRootElementResized = (0, react_1.useCallback)(function (args) {
        var _a;
        var contentRect = (_a = args.find(function (it) { return it.contentRect; })) === null || _a === void 0 ? void 0 : _a.contentRect;
        if (contentRect) {
            setRootSize({
                width: contentRect.width,
                height: contentRect.height
            });
            if (imageSize) {
                setCalculatedHeight(contentRect.width / imageSize.width * imageSize.height);
            }
        }
    }, [setRootSize, imageSize]);
    var onRootElementRendered = (0, react_1.useCallback)(function (element) {
        if (element) {
            rootElement.current = element;
            var observer = new ResizeObserver(onRootElementResized);
            observer.observe(element);
            resizeObserver.current = observer;
            setRootSize({
                width: element.offsetWidth,
                height: element.offsetHeight
            });
            if (imageSize) {
                setCalculatedHeight(element.offsetWidth / imageSize.width * imageSize.height);
            }
        }
    }, [setRootSize, imageSize, rootElement, resizeObserver]);
    (0, react_1.useEffect)(function () {
        var image = new Image();
        image.onload = function () { return onImageLoaded(image); };
        image.src = imageSrc;
    }, [imageSrc, rows, columns]);
    var onTileMouseDown = (0, react_1.useCallback)(function (tile, event) {
        var _a, _b;
        if (!tile.solved) {
            if (event.type === 'touchstart') {
                document.documentElement.style.setProperty('overflow', 'hidden');
            }
            var eventPos = {
                x: (_a = event.pageX) !== null && _a !== void 0 ? _a : event.touches[0].pageX,
                y: (_b = event.pageY) !== null && _b !== void 0 ? _b : event.touches[0].pageY
            };
            draggingTile.current = {
                tile: tile,
                elem: event.target,
                mouseOffsetX: eventPos.x - event.target.getBoundingClientRect().x,
                mouseOffsetY: eventPos.y - event.target.getBoundingClientRect().y
            };
            event.target.classList.add('jigsaw-puzzle__piece--dragging');
        }
    }, [draggingTile]);
    var onRootMouseMove = (0, react_1.useCallback)(function (event) {
        var _a, _b;
        if (draggingTile.current) {
            event.stopPropagation();
            event.preventDefault();
            var eventPos = {
                x: (_a = event.pageX) !== null && _a !== void 0 ? _a : event.touches[0].pageX,
                y: (_b = event.pageY) !== null && _b !== void 0 ? _b : event.touches[0].pageY
            };
            var draggedToRelativeToRoot = {
                x: clamp(eventPos.x - rootElement.current.getBoundingClientRect().left - draggingTile.current.mouseOffsetX, 0, rootSize.width - draggingTile.current.elem.offsetWidth),
                y: clamp(eventPos.y - rootElement.current.getBoundingClientRect().top - draggingTile.current.mouseOffsetY, 0, rootSize.height - draggingTile.current.elem.offsetHeight)
            };
            draggingTile.current.elem.style.setProperty('left', "".concat(draggedToRelativeToRoot.x, "px"));
            draggingTile.current.elem.style.setProperty('top', "".concat(draggedToRelativeToRoot.y, "px"));
        }
    }, [draggingTile, rootSize]);
    var onRootMouseUp = (0, react_1.useCallback)(function (event) {
        var _a;
        if (draggingTile.current) {
            if (event.type === 'touchend') {
                document.documentElement.style.removeProperty('overflow');
            }
            (_a = draggingTile.current) === null || _a === void 0 ? void 0 : _a.elem.classList.remove('jigsaw-puzzle__piece--dragging');
            var draggedToPercentage_1 = {
                x: clamp(draggingTile.current.elem.offsetLeft / rootSize.width, 0, 1),
                y: clamp(draggingTile.current.elem.offsetTop / rootSize.height, 0, 1)
            };
            var draggedTile_1 = draggingTile.current.tile;
            var targetPositionPercentage_1 = {
                x: draggedTile_1.correctPosition % columns / columns,
                y: Math.floor(draggedTile_1.correctPosition / columns) / rows
            };
            var isSolved_1 = Math.abs(targetPositionPercentage_1.x - draggedToPercentage_1.x) <= solveTolerancePercentage &&
                Math.abs(targetPositionPercentage_1.y - draggedToPercentage_1.y) <= solveTolerancePercentage;
            setTiles(function (prevState) {
                var newState = __spreadArray(__spreadArray([], prevState.filter(function (it) { return it.correctPosition !== draggedTile_1.correctPosition; }), true), [
                    __assign(__assign({}, draggedTile_1), { currentPosXPerc: !isSolved_1 ? draggedToPercentage_1.x : targetPositionPercentage_1.x, currentPosYPerc: !isSolved_1 ? draggedToPercentage_1.y : targetPositionPercentage_1.y, solved: isSolved_1 })
                ], false);
                if (newState.every(function (tile) { return tile.solved; })) {
                    onSolved();
                }
                return newState;
            });
            draggingTile.current = undefined;
        }
    }, [draggingTile, setTiles, rootSize, onSolved]);
    return react_1.default.createElement("div", { ref: onRootElementRendered, onTouchMove: onRootMouseMove, onMouseMove: onRootMouseMove, onTouchEnd: onRootMouseUp, onMouseUp: onRootMouseUp, onTouchCancel: onRootMouseUp, onMouseLeave: onRootMouseUp, className: "jigsaw-puzzle", style: { height: !calculatedHeight ? undefined : "".concat(calculatedHeight, "px") }, onDragEnter: function (event) {
            event.stopPropagation();
            event.preventDefault();
        }, onDragOver: function (event) {
            event.stopPropagation();
            event.preventDefault();
        } }, tiles && rootSize && imageSize && tiles.map(function (tile) {
        return react_1.default.createElement("div", { draggable: false, onMouseDown: function (event) { return onTileMouseDown(tile, event); }, onTouchStart: function (event) { return onTileMouseDown(tile, event); }, key: tile.correctPosition, className: "jigsaw-puzzle__piece ".concat(tile.solved ? ' jigsaw-puzzle__piece--solved' : '', " "), style: {
                position: 'absolute',
                height: "".concat(1 / rows * 100, "%"),
                width: "".concat(1 / columns * 100, "%"),
                backgroundImage: "url(".concat(imageSrc, ")"),
                backgroundSize: "".concat(rootSize.width, "px ").concat(rootSize.height, "px"),
                backgroundPositionX: "".concat(tile.correctPosition % columns / (columns - 1) * 100, "%"),
                backgroundPositionY: "".concat(Math.floor(tile.correctPosition / columns) / (rows - 1) * 100, "%"),
                left: "".concat(tile.currentPosXPerc * rootSize.width, "px"),
                top: "".concat(tile.currentPosYPerc * rootSize.height, "px")
            } });
    }));
};
exports.JigsawPuzzle = JigsawPuzzle;

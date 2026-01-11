"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Puzzle = void 0;
var __1 = require("../");
require("../jigsaw-puzzle.css");
require("./jigsaw-puzzle.css");
var meta = {
    component: __1.JigsawPuzzle,
    title: 'react-jigsaw-puzzle',
    argTypes: {
        imageSrc: {
            description: 'Source of the image. Can be any URL or relative path.',
            type: 'string'
        },
        rows: {
            defaultValue: 3,
            description: 'The amount of rows the puzzle will have.',
            type: 'number'
        },
        columns: {
            defaultValue: 4,
            description: 'The amount of columns the puzzle with have.',
            type: 'number'
        },
        onSolved: {
            description: 'Called when the puzzle is solved.',
            action: 'solved'
        }
    }
};
exports.default = meta;
exports.Puzzle = {
    args: {
        imageSrc: 'https://images.unsplash.com/photo-1595045051853-05ef47bdfdbe?3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80'
    }
};

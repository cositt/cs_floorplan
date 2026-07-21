/** @odoo-module **/

import { Component, useState, onWillStart, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";

const MIN_WIDTH = 60;
const MIN_HEIGHT = 50;
const ROOM_FIELDS = [
    "name", "tipo", "capacidad", "ocupados", "disponibles", "state",
    "pos_x", "pos_y", "width", "height", "resident_ids",
];

export class FloorplanCanvas extends Component {
    static template = "cs_floorplan.FloorplanCanvas";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.canvasRef = useRef("canvas");

        this.state = useState({
            rooms: [],
            canEdit: false,
            editMode: false,
        });

        onWillStart(async () => {
            this.state.canEdit = await user.hasGroup("cs_floorplan.group_cs_floorplan_manager");
            await this.loadRooms();
        });
    }

    get floorId() {
        return this.props.record.resId;
    }

    async loadRooms() {
        if (!this.floorId) {
            this.state.rooms = [];
            return;
        }
        const rooms = await this.orm.searchRead(
            "cs.room",
            [["floor_id", "=", this.floorId]],
            ROOM_FIELDS,
        );
        const residentIds = [...new Set(rooms.flatMap((r) => r.resident_ids))];
        let residentsById = {};
        if (residentIds.length) {
            const residents = await this.orm.read("cs.resident", residentIds, ["name", "state"]);
            residentsById = Object.fromEntries(residents.map((r) => [r.id, r]));
        }
        this.state.rooms = rooms.map((r) => ({
            ...r,
            residents: r.resident_ids
                .map((id) => residentsById[id])
                .filter((r2) => r2 && r2.state === "activo"),
        }));
    }

    toggleEditMode() {
        this.state.editMode = !this.state.editMode;
    }

    roomColor(room) {
        if (room.state === "mantenimiento" || room.state === "cerrada") {
            return "room-maintenance";
        }
        if (room.ocupados <= 0) {
            return "room-free";
        }
        if (room.disponibles > 0) {
            return "room-partial";
        }
        return "room-full";
    }

    async onNewRoom() {
        await this.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "cs.room",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
                context: {
                    default_floor_id: this.floorId,
                    default_residence_id: this.props.record.data.residence_id?.id,
                },
            },
            { onClose: () => this.loadRooms() },
        );
    }

    onRoomPointerDown(ev, room) {
        if (!this.state.editMode) {
            return;
        }
        ev.preventDefault();
        const isResize = ev.target.classList.contains("o_floorplan_resize_handle");
        const startX = ev.clientX;
        const startY = ev.clientY;
        const origX = room.pos_x;
        const origY = room.pos_y;
        const origW = room.width;
        const origH = room.height;

        const onMove = (moveEv) => {
            const dx = moveEv.clientX - startX;
            const dy = moveEv.clientY - startY;
            if (isResize) {
                room.width = Math.max(MIN_WIDTH, origW + dx);
                room.height = Math.max(MIN_HEIGHT, origH + dy);
            } else {
                room.pos_x = Math.max(0, origX + dx);
                room.pos_y = Math.max(0, origY + dy);
            }
        };
        const onUp = async () => {
            window.removeEventListener("pointermove", onMove);
            window.removeEventListener("pointerup", onUp);
            await this.orm.write("cs.room", [room.id], {
                pos_x: room.pos_x,
                pos_y: room.pos_y,
                width: room.width,
                height: room.height,
            });
        };
        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
    }

    onResidentDragStart(ev, resident) {
        ev.dataTransfer.setData("text/resident-id", String(resident.id));
        ev.dataTransfer.effectAllowed = "move";
    }

    onResidentClick(ev, resident) {
        if (this.state.editMode) {
            return;
        }
        ev.stopPropagation();
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cs.resident",
            res_id: resident.id,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }

    onRoomDragOver(ev) {
        if (ev.dataTransfer.types.includes("text/resident-id")) {
            ev.preventDefault();
        }
    }

    async onRoomDrop(ev, room) {
        ev.preventDefault();
        const residentId = Number(ev.dataTransfer.getData("text/resident-id"));
        if (!residentId) {
            return;
        }
        if (room.residents.some((r) => r.id === residentId)) {
            return;
        }
        if (room.disponibles <= 0) {
            this.notification.add(_t("Esa habitación no tiene plazas libres."), { type: "danger" });
            return;
        }
        try {
            await this.orm.write("cs.resident", [residentId], { room_id: room.id });
            await this.loadRooms();
        } catch (error) {
            this.notification.add(_t("No se pudo mover al residente."), { type: "danger" });
        }
    }
}

registry.category("view_widgets").add("floorplan_canvas", {
    component: FloorplanCanvas,
});

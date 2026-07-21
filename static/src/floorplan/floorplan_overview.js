/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const ROOM_FIELDS = [
    "name", "tipo", "capacidad", "ocupados", "disponibles", "state",
    "pos_x", "pos_y", "width", "height", "resident_ids", "floor_id",
];

export class FloorplanOverview extends Component {
    static template = "cs_floorplan.FloorplanOverview";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ floors: [] });
        onWillStart(() => this.loadFloors());
    }

    get residenceId() {
        return this.props.action.params?.residence_id;
    }

    async loadFloors() {
        if (!this.residenceId) {
            this.state.floors = [];
            return;
        }
        const floors = await this.orm.searchRead(
            "cs.residence.floor",
            [["residence_id", "=", this.residenceId]],
            ["name", "sequence"],
            { order: "sequence, name" },
        );
        const floorIds = floors.map((floor) => floor.id);
        const rooms = floorIds.length
            ? await this.orm.searchRead("cs.room", [["floor_id", "in", floorIds]], ROOM_FIELDS)
            : [];
        const residentIds = [...new Set(rooms.flatMap((room) => room.resident_ids))];
        let residentsById = {};
        if (residentIds.length) {
            const residents = await this.orm.read("cs.resident", residentIds, ["name", "state"]);
            residentsById = Object.fromEntries(residents.map((resident) => [resident.id, resident]));
        }
        this.state.floors = floors.map((floor) => ({
            ...floor,
            rooms: rooms
                .filter((room) => room.floor_id && room.floor_id[0] === floor.id)
                .map((room) => ({
                    ...room,
                    residents: room.resident_ids
                        .map((id) => residentsById[id])
                        .filter((resident) => resident && resident.state === "activo"),
                })),
        }));
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

    onResidentClick(ev, resident) {
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

    onFloorClick(floor) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cs.residence.floor",
            res_id: floor.id,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("cs_floorplan_overview", FloorplanOverview);

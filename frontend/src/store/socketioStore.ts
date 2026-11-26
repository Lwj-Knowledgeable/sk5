import { defineStore } from 'pinia';
import { io } from 'socket.io-client';
interface L2tpTraffic {
    interface: string;
    rx: number;
    tx: number;
}
export const useSocketioStore = defineStore('socketio', {
    state: () => ({
        socketio: null as any | null,
        isConnected: false as boolean,
        l2tpTrafficList: [] as L2tpTraffic[],
    }),
    actions: {
        connect(): any {
            if(this.socketio) return;
            this.socketio = io();
            this.socketio?.on('l2tp_traffic', (data: any) => {
                // console.log('l2tp_traffic-id:',Math.random(), data,);
                this.l2tpTrafficList = data.data;
                // console.log('l2tpTrafficList:',this.l2tpTrafficList);
            });
        },
        disconnect() {
            this.socketio?.off('l2tp_traffic');
            this.socketio?.disconnect();
            this.socketio = null;
        },
    },
    getters: {
        getSocketio(): any {
            return this.socketio;
        },
    },
});
import {Injectable} from "@angular/core";
import {IAppState} from "../configure";
import {NgRedux} from "@angular-redux/store";
import {IChargerCaseFan, System} from "../../system";
import {iChargerService} from "../../../services/icharger.service";
import {UIActions} from "./ui";
import {Observable} from "rxjs/Observable";
import {AppModule} from "../../../app/app.module";
import {compareTwoMaps} from "../../../utils/helpers";
import {ISystem} from "../reducers/system";
import {forkJoin} from "rxjs/observable/forkJoin";
import {of} from "rxjs/observable/of";

@Injectable()
export class SystemActions {
    static FETCH_SYSTEM: string = "FETCH_SYSTEM";
    static START_FETCH: string = "START_FETCH";
    static END_FETCH: string = "END_FETCH";
    static SAVE_SETTINGS: string = "SAVE_SETTINGS";
    static UPDATE_SETTINGS_VALUE: string = "UPDATE_SETTINGS_VALUE";
    static FETCH_CASE_FAN: string = "FETCH_CASE_FAN";
    static UPDATE_CASE_FAN: string = "UPDATE_CASE_FAN";

    private _chargerService: iChargerService;

    constructor(private ngRedux: NgRedux<IAppState>,
                private uiActions: UIActions) {
    }

    private chargerService() {
        if (this._chargerService == null) {
            this._chargerService = AppModule.injector.get(iChargerService);
        }
        return this._chargerService;
    }

    fetchSystemFromCharger(callback = null) {
        this.ngRedux.dispatch({
            type: SystemActions.FETCH_SYSTEM
        });

        let chargerService = this.chargerService();
        if (chargerService) {
            let system_request = chargerService.getSystem();
            let case_request = chargerService.getCaseFan();

            forkJoin(
                system_request,
                case_request
            ).subscribe(v => {
                // We get a LIST of responses.
                // The case_fan response is dispatched to redux by the getCaseFan call.
                let system_object = v[0];
                // let case_fan_info = v[1];
                this.ngRedux.dispatch(this.endFetchAction(system_object));
                if (callback) {
                    callback();
                }
            }, (error) => {
                this.uiActions.setErrorMessage(error);
            });
        }
    }

    userChangedValue(change) {
        this.ngRedux.dispatch({
            type: SystemActions.UPDATE_SETTINGS_VALUE,
            payload: change
        });
    }

    updateSystemValue(key: string, value: any) {
        let change = [];
        change[key] = value;
        this.userChangedValue(change);
    }

    saveSystemSettings(systemObject: ISystem): Observable<ISystem> {
        let sysValues = systemObject.system;
        if (sysValues.has_case_fan) {
            let fanValues = systemObject.case_fan;
            this.chargerService().saveCaseFan(fanValues).subscribe()
        }

        return this.chargerService().saveSystem(sysValues).map((s: System) => {
            this.ngRedux.dispatch(this.endFetchAction(s));
        });
    }

    startFetch() {
        this.ngRedux.dispatch({
            type: SystemActions.START_FETCH
        });
    }

    endFetchAction(systemObject: System, callback = null) {
        return {
            type: SystemActions.END_FETCH,
            payload: systemObject,
        };
    }

    updateCaseFan(case_fan_state: any) {
        // console.log(`See case fan state: ${JSON.stringify(case_fan_state)}`);
        let existing = this.ngRedux.getState().system.case_fan;
        let comparison_result = compareTwoMaps(existing, case_fan_state);
        if (comparison_result.length > 0) {
            console.log("Case fan state differs: " + comparison_result.join(", "));
            this.ngRedux.dispatch({
                type: SystemActions.UPDATE_CASE_FAN,
                payload: case_fan_state
            })
        }
    }
}
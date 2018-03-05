import {BrowserModule} from "@angular/platform-browser";
import {HttpModule} from "@angular/http";
import {ErrorHandler, Injector, NgModule} from "@angular/core";
import {IonicStorageModule} from "@ionic/storage";
import {IonicApp, IonicErrorHandler, IonicModule} from "ionic-angular";
import {MyApp} from "./app.component";
import {HomePage} from "../pages/home/home";
import {iChargerService} from "../services/icharger.service";
import {ConfigPage} from "../pages/config/config-page";
import {ChannelComponent} from "../components/channel/channel";
import {ChargerStatusComponent} from "../components/charger-status/charger-status";
import {PresetListPage} from "../pages/preset-list/preset-list";
import {PresetPage} from "../pages/preset/preset";
import {PresetChargePage} from "../pages/preset-charge/preset-charge";
import {PresetStoragePage} from "../pages/preset-storage/preset-storage";
import {PresetDischargePage} from "../pages/preset-discharge/preset-discharge";
import {PresetCyclePage} from "../pages/preset-cycle/preset-cycle";
import {DynamicDisable} from "../utils/directives";
import {ChargeOptionsPage} from "../pages/charge-options/charge-options";
import {ConnectionStateComponent} from "../components/connection-state/connection-state";
import {ChannelVoltsComponent} from "../components/channel-volts/channel-volts";
import {ChannelIRComponent} from "../components/channel-volts/channel-ir";
import {StatusBar} from "@ionic-native/status-bar";
import {SplashScreen} from "@ionic-native/splash-screen";
import {ContactPage} from "../pages/contact/contact";
import {PresetBalancePage} from "../pages/preset-balance/preset-balance";
import {TabsPage} from "../pages/tabs/tabs";
import {DevToolsExtension, NgRedux, NgReduxModule} from "@angular-redux/store";
import {configureAppStateStore, IAppState} from "../models/state/configure";
import {ConfigStoreProvider} from '../providers/config-store/config-store';
import {ChargerActions} from "../models/state/actions/charger";
import {UIActions} from "../models/state/actions/ui";
import {ConfigurationEpics} from "../models/state/epics/configuration";
import {ConfigurationActions} from "../models/state/actions/configuration";
import {SystemActions} from "../models/state/actions/system";
import {SystemSettingsPageModule} from "../pages/system-settings/system-settings.module";
import {ComponentsModule} from "../components/components.module";
import {Vibration} from "@ionic-native/vibration";
import {LocalNotifications} from "@ionic-native/local-notifications";
import {Zeroconf} from "@ionic-native/zeroconf";
import {NetworkPage} from "../pages/network-page/network-page";
import {UtilsModule} from "../utils/utils.module";
import {ElectricNetworkService} from "../services/network.service";
import {NetworkWizHomePage} from "../pages/network-wiz-home/network-wiz-home";

export const firebaseConfig = {
    apiKey: "AIzaSyDDfmaQMyk_8UgQmcTJa8u2Ruv3emGEKAc",
    authDomain: "https://electric-app-e4963.firebaseio.com",
    databaseURL: "https://electric-app-e4963.firebaseio.com",
    storageBucket: "electric-app-e4963.appspot.com",
    messagingSenderId: '811177846859'
};

let config = {
    platforms: {
        ios: {
            // These are SUPPOSED To fix the borked toolbar on iOS. They don't on os11, that's for sure.
            statusbarPadding: true,
            tabsHideOnSubPages: true,
        }
    }
};

@NgModule({
    declarations: [
        MyApp,
        ContactPage,
        ConfigPage,
        HomePage,
        DynamicDisable,
        ChannelComponent,
        ChannelVoltsComponent,
        ChannelIRComponent,
        ConnectionStateComponent,
        PresetListPage,
        PresetPage,
        PresetChargePage,
        PresetStoragePage,
        PresetDischargePage,
        PresetBalancePage,
        TabsPage,
        PresetCyclePage,
        ChargeOptionsPage,
        NetworkPage,
        NetworkWizHomePage,
        ChargerStatusComponent,
    ],
    imports: [
        BrowserModule,
        HttpModule,
        // BrowserAnimationsModule,
        UtilsModule,
        NgReduxModule,
        ComponentsModule,
        SystemSettingsPageModule,
        IonicModule.forRoot(MyApp, config),
        // AngularFireModule.initializeApp(firebaseConfig),
        IonicStorageModule.forRoot(),
    ],
    bootstrap: [IonicApp],
    entryComponents: [
        MyApp,
        HomePage,
        ConfigPage,
        NetworkPage,
        NetworkWizHomePage,
        PresetListPage,
        PresetPage,
        PresetChargePage,
        PresetStoragePage,
        PresetDischargePage,
        PresetCyclePage,
        ChargeOptionsPage,
        ChannelVoltsComponent,
        ChannelIRComponent,
        ConnectionStateComponent,
    ],
    providers: [
        ChargerActions,
        UIActions,
        ConfigStoreProvider,
        ConfigurationActions,
        SystemActions,
        ConfigurationEpics,
        StatusBar,
        SplashScreen,
        Vibration,
        Zeroconf,
        LocalNotifications,
        ElectricNetworkService,
        {provide: iChargerService, useClass: iChargerService},
        {provide: ErrorHandler, useClass: IonicErrorHandler},
        ConfigStoreProvider
    ]
})
export class AppModule {
    static injector: Injector;

    constructor(ngRedux: NgRedux<IAppState>,
                injector: Injector,
                configEpic: ConfigurationEpics,
                devTools: DevToolsExtension) {
        configureAppStateStore(ngRedux, configEpic, devTools);
        AppModule.injector = injector;
    }
}

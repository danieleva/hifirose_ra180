# Home Assistant Custom Component for controlling HifiRose RA180 amplifier

This is very much experimental, hifirose apis are undocumented, this module is based on data obtained by reverse engineering.
The ra180 library in this module covers 90% of RoseAmp Connector app functions.
There's plenty of room for improvement. Hopefully hifirose will publish some docs for their api.

For this component to work, you'll need to setup the amplifier using RoseAmp Connector app and configure it to join your wifi network.
Take note of the amplifier IP from the app and use it to configure the integration
Then you need to add the following to your `configuration.yaml` file:

```
media_player:
  - platform: hifirose_ra180
    device: <amplifier ip address from RoseAmp Connecto app>
    name: RA180
```

Restart Home Assistant, and see you have a new media_player entity for your RA180.


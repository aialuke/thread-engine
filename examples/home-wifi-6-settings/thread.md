# home-wifi-6-settings

conversation_id: 2101603601143803913
account: @exitzerocode

---

Most home wifi routers get plugged in once and then left alone for years.

A family was paying $90/month for a "premium speed" upgrade because Zoom kept freezing mid-call and YouTube kept buffering on 4K every single evening.

Their IT-guy came over and spent just 10 minutes in the router's admin panel — a page most people have never even opened once.

He didn't upgrade the plan.
Didn't buy a new router.
Didn't call the ISP.
Didn't run a single speed test.

He changed 6 settings.

Zoom stopped freezing immediately. YouTube stopped buffering in 4K. Every device in the house — phones, laptops, the smart TV, even the video doorbell — got noticeably faster at the exact same time.

"Your Wi-Fi was never too slow for this. It was just never configured past the day the technician plugged it in — and nobody, not your ISP, not the store that sold you the router, not the box on the wall, was ever going to tell you the fix was free."

🧵 Here are the 6 settings that fixed it:

---

Setting 1: Wi-Fi Channel Selection

Routers auto-select a wireless channel on setup day and then never touch it again — even as neighbors' routers pile onto that same channel over the following years.

In dense neighborhoods or apartment buildings, this creates constant interference nobody can see, just slow and inconsistent speeds that seem to happen "for no reason."

Go into the router admin panel (usually 192.168.1.1 or 192.168.0.1 typed into a browser) and find Wireless Settings > Channel.

Switch it from "Auto" to a manually chosen less-crowded channel — 1, 6, or 11 for 2.4GHz is usually the safest bet.

This single change cut out a huge amount of the random buffering within minutes.

Most routers have been quietly fighting for airspace with five other networks this entire time.

---

Setting 2: 5GHz vs 2.4GHz Band Priority

Most devices default to connecting to whichever band they saw first — and once connected, they never automatically switch, even when a faster band is sitting right there unused.

The family's smart TV and laptop were both stuck on the slower, more congested 2.4GHz band the entire time, while the fast 5GHz band sat mostly empty.

Go to Wireless Settings and rename the 5GHz network something distinct from the 2.4GHz one (instead of one shared name for both).

Then manually reconnect devices used for streaming or video calls to the 5GHz network specifically.

5GHz carries far more data at closer range — perfect for Zoom calls and 4K video sitting in the same room as the router.

This alone fixed the majority of the Zoom freezing on its own.

---

Setting 3: QoS (Quality of Service)

Without QoS enabled, the router treats every device and every task with equal priority — meaning a phone downloading an app update can throttle a Zoom call happening at the exact same moment.

Most routers have this feature sitting disabled by default, buried in an "Advanced" tab nobody opens.

Go to Advanced Settings > QoS (Quality of Service) and turn it ON.

Set video calls and streaming apps as high priority if the router allows manual tagging — most modern routers do this automatically once enabled.

This stops random background downloads and updates from stealing bandwidth mid-call.

Zoom calls stopped freezing even when three other people were using the internet in the house simultaneously.

---

Setting 4: Firmware Update

Routers almost never update themselves automatically, and most people have no idea firmware updates are even a thing that exists for their router.

An outdated firmware version means the router is missing years of speed improvements, security patches, and bug fixes the manufacturer already released.

Go to Administration or System Settings and look for "Firmware Update" or "Router Update."

Click check for updates, and install the latest version if one is available — this usually takes 5-10 minutes and the router restarts on its own.

Some routers found updates that hadn't been installed in over 3 years.

This alone resolved random disconnects that everyone had just learned to live with.

---

Setting 5: DNS Server Change

Every device on the network uses whatever DNS server the ISP auto-assigns by default — and most ISP-provided DNS servers are slower and less reliable than free public alternatives.

DNS is what translates a website name into an actual connection, so a slow DNS server adds delay to literally everything, every single time you load anything.

Go to Wireless Settings or WAN Settings and find "DNS Server."

Switch it manually to a faster public option like Cloudflare (1.1.1.1) or Google DNS (8.8.8.8).

Pages started loading noticeably faster across every device the moment this changed.

It's a 30-second fix nobody ever knows to look for.

---

Setting 6: Connected Devices Cleanup

Over years of use, routers accumulate dozens of "ghost" devices still technically connected or remembered — old phones, guests' laptops, devices that were sold or thrown away long ago.

Each of these can still be holding a reserved connection slot or occasionally reconnecting in the background, quietly eating bandwidth nobody's using.

Go to Connected Devices or Attached Devices in the admin panel and review the full list.

Remove or block anything you don't recognize, and forget any old devices no longer in the house.

The family found 11 devices still listed that hadn't physically been in their home in over a year.

Clearing this list freed up bandwidth that had been sitting locked up the entire time.

ok so to build the musical engine the things that we need to do:

**find the instruments**
which vst will we use?

can we use VSTs? for orchestra thats the gold standard right?

if we use VSTs, will this work as a standalone web product?

will we bounce or keep vst? do we want to keep the musical engine generating music real time or prepare a bunch of musically pleasing and well connected musical ingredients bounced that will just play in as audio files and switch on viewport changes?

will this generate music on real time or play audios?

if this is a web app that has to run ideally client side (no costs), what limitations should we account for in terms of memory? what is the best practice here?

when we zoom out and we see everything, what do we play?

how should we structure the harmony?
should the chords move around(simple harmony like interstellar, or playing with john williams more complex harmonic structures when signals move into specific thresholds or patterns) or simple droid soundscape that adds instruments as signal come in(no rythmic structure => no quantize, low latency and more real time data feeling)? or else?


**ideas**
I think you should use the approach that we have with Serious Sam, which is starting with an ambient and then introducing percussive elements. There is one shared tempo. I actually don't know how the music engine works in Serious Sam. I think they are just fading in and out different samples from different like, literally different music that represents different phases of the map. So when it's like chill, when it's like fighting time, or it's like even more violent fighting time. So I think we could have this different, this is the same approach of intensity, which basically we can define the term like a spectrum of parameters. And the low end of the spectrum is the bass without percussions, just relaxing almost meditation like drone ambient soundscape. And when we move towards the higher end of intensity, we start adding taiko drums, we start adding brass, stabs, we start adding ostinato strings, stuff like that.